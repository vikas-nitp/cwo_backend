"""
Offer Engine Service - Core business logic

Handles:
- Base fare generation
- Discount calculation
- Price strip generation (10-day)
- Auth-based offer gating
- Tile labeling based on card selection
"""

from datetime import date, timedelta
from typing import Dict, List, Optional

from app.models.schemas import Offer, OfferCard, PriceStripItem, SearchSummary
from app.core.config import OfferEngineConfig, PriceStripConfig, PLATFORM_URLS


class BaseFareGenerator:
    """Generates deterministic base fares based on route and date"""

    @staticmethod
    def generate(from_code: str, to_code: str, travel_date: date) -> int:
        route_seed = sum(ord(c) for c in (from_code + to_code))
        date_seed = travel_date.toordinal()
        total_seed = route_seed + date_seed
        
        range_size = OfferEngineConfig.MAX_BASE_FARE - OfferEngineConfig.MIN_BASE_FARE
        return OfferEngineConfig.MIN_BASE_FARE + (total_seed % range_size)


class PriceStripGenerator:
    """Generates N-day price strip starting from selected date (configurable)"""

    @staticmethod
    def generate(
        from_code: str,
        to_code: str,
        start_date: date,
        platform_prices: Optional[Dict[str, int]] = None,
    ) -> List[PriceStripItem]:
        if not platform_prices:
            platform_prices = {
                "MakeMyTrip_web": 1575,
                "MakeMyTrip_app": 1545,
                "Ixigo_web": 1600,
                "Ixigo_app": 1565,
            }
        
        route_seed = sum(ord(c) for c in (from_code + to_code))
        
        strip = []
        for day_offset in range(PriceStripConfig.STRIP_DAYS_COUNT):
            current_date = start_date + timedelta(days=day_offset)
            date_str = current_date.strftime(PriceStripConfig.DATE_FORMAT)
            date_seed = current_date.toordinal()
            
            prices = {}
            for platform, base_price in platform_prices.items():
                platform_seed = sum(ord(c) for c in platform)
                combined_seed = route_seed + date_seed + platform_seed
                # Deterministic variation within configured range
                var_range = PriceStripConfig.PRICE_VAR_MAX - PriceStripConfig.PRICE_VAR_MIN
                variation = PriceStripConfig.PRICE_VAR_MIN + (combined_seed % (var_range + 1))
                prices[platform] = base_price + (variation if combined_seed % 2 == 0 else -variation // 2)
            
            best_price = min(prices.values()) if prices else 0
            
            strip.append(PriceStripItem(
                date=date_str,
                price=best_price,
                prices=prices if prices else None,
            ))
        
        return strip


class DiscountCalculator:
    """Calculates discount amount with strict rules"""

    @staticmethod
    def calculate(offer: Offer, base_price: int) -> int:
        """
        Calculate discount amount.
        
        Rules:
        - if base_price < min_txn => discount = 0
        - FLAT: discount_value capped by max_discount if max_discount > 0
        - PERCENT: (base_price * discount_value/100) capped by max_discount if max_discount > 0
        """
        if base_price < offer.min_txn:
            return 0

        if offer.discount_type == "FLAT":
            # FLAT discount: use discount_value, cap by max_discount if set
            discount = offer.discount_value
            if offer.max_discount > 0:
                discount = min(discount, offer.max_discount)
            return int(discount)
        
        elif offer.discount_type == "PERCENT":
            # PERCENT discount: (base_price * %) capped by max_discount if set
            raw_discount = (base_price * offer.discount_value) / 100.0
            if offer.max_discount > 0:
                discount = min(raw_discount, offer.max_discount)
            else:
                discount = raw_discount
            return int(discount)
        
        return 0


class FinalPriceCalculator:
    """Calculates final price with deterministic variation"""

    @staticmethod
    def calculate(offer: Offer, base_price: int, discount: int) -> tuple[int, int]:
        """
        Calculate final price with variation.
        
        Args:
            offer: The offer to price
            base_price: Base fare for route/date
            discount: Computed discount amount
            
        Returns:
            (final_price, savings) tuple
            
        Pricing logic:
        - final = base_fare - discount - variation
        - variation: deterministic per offer_id, range ₹100–₹300
        - minimum final_price: ₹999
        - savings = base_fare - final_price
        """
        final = base_price - discount
        
        # Compute deterministic variation per offer_id (range: ₹100–₹300)
        variation = OfferEngineConfig.MIN_PRICE_VAR + (
            sum(ord(c) for c in offer.offer_id) % 
            (OfferEngineConfig.MAX_PRICE_VAR - OfferEngineConfig.MIN_PRICE_VAR + 1)
        )
        
        # Apply variation and enforce minimum
        final = max(OfferEngineConfig.MIN_FINAL_PRICE, final - variation)
        
        # Savings is the difference between base and final
        savings = max(0, base_price - final)
        
        return final, savings


class AuthGatekeeper:
    """
    Handles auth-based offer gating based on feature flags.
    
    Feature Flag Logic:
    - authEnabled=false → All offers visible (no locking)
    - authEnabled=true + offerLockingEnabled=false → All offers visible
    - authEnabled=true + offerLockingEnabled=true → Lock offers for guests
    """

    @staticmethod
    def gate_offers(
        offer_cards: List[OfferCard],
        is_authenticated: bool,
        offer_locking_enabled: bool = True,
    ) -> List[OfferCard]:
        """
        Apply offer gating based on auth status and feature flags.
        
        Args:
            offer_cards: List of offer cards
            is_authenticated: Whether user is authenticated
            offer_locking_enabled: Whether offer locking is enabled (from feature flags)
        """
        # If locking is disabled, show all offers unlocked
        if not offer_locking_enabled:
            for card in offer_cards:
                card.locked = False
            return offer_cards
        
        # Authenticated users see all offers unlocked
        if is_authenticated:
            for card in offer_cards:
                card.locked = False
            return offer_cards
        
        # Guest users: limit visibility when locking is enabled
        visible_count = 0
        unlocked_limit = OfferEngineConfig.UNLOCKED_OFFERS_FOR_GUEST
        
        for card in offer_cards:
            if card.label == "Default Offer" or visible_count < unlocked_limit:
                card.locked = False
                visible_count += 1
            else:
                card.locked = True
        
        return offer_cards


class TileLabeler:
    """
    Labels offer tiles based on card selection rules.
    
    RULES:
    - 0 cards: max 2 tiles → "Best Offer" (best bank) + "Default Offer" (best Any)
    - 1 card: max 3 tiles → "Your Card Offer" + "Best Offer" (other bank if better) + "Default Offer"
    - 2 cards (different savings): max 3 tiles → "Best Among Selected" + "Best Offer" (other if better) + "Default Offer"
    - 2 cards (same savings): max 4 tiles → both selected cards + "Best Offer" (other if better) + "Default Offer"
    """

    @staticmethod
    def label_offers(
        offer_cards: List[OfferCard],
        selected_banks: Optional[List[str]] = None,
    ) -> List[OfferCard]:
        if not offer_cards:
            return []
        
        # Normalize selected banks
        selected_upper = set(b.upper() for b in selected_banks) if selected_banks else set()
        
        # Partition: default (Any) vs bank-specific
        default_offers = [c for c in offer_cards if c.bank.upper() == "ANY"]
        bank_offers = [c for c in offer_cards if c.bank.upper() != "ANY"]
        
        # Sort by savings descending
        bank_offers.sort(key=lambda c: c.savings, reverse=True)
        default_offers.sort(key=lambda c: c.savings, reverse=True)
        
        labeled = []
        
        # ═══════════════════════════════════════════════════════════
        # CASE 0: No cards selected → max 2 tiles
        # ═══════════════════════════════════════════════════════════
        if not selected_upper:
            if bank_offers:
                bank_offers[0].label = "Best Offer"
                labeled.append(bank_offers[0])
            if default_offers:
                default_offers[0].label = "Default Offer"
                labeled.append(default_offers[0])
            return labeled
        
        # ═══════════════════════════════════════════════════════════
        # CASE 1+: Cards selected
        # ═══════════════════════════════════════════════════════════
        selected_offers = [c for c in bank_offers if c.bank.upper() in selected_upper]
        non_selected_offers = [c for c in bank_offers if c.bank.upper() not in selected_upper]
        
        # Sort selected by savings
        selected_offers.sort(key=lambda c: c.savings, reverse=True)
        
        # ─────────────────────────────────────────────────────────────
        # CASE 1: 1 card selected → max 3 tiles
        # ─────────────────────────────────────────────────────────────
        if len(selected_upper) == 1:
            if selected_offers:
                selected_offers[0].label = "Your Card Offer"
                labeled.append(selected_offers[0])
            
            # Add best non-selected if better savings
            if non_selected_offers:
                best_other = non_selected_offers[0]
                best_selected_savings = selected_offers[0].savings if selected_offers else 0
                if best_other.savings > best_selected_savings:
                    best_other.label = "Best Offer"
                    labeled.append(best_other)
            
            # Add best default
            if default_offers:
                default_offers[0].label = "Default Offer"
                labeled.append(default_offers[0])
            
            return labeled
        
        # ─────────────────────────────────────────────────────────────
        # CASE 2: 2 cards selected → max 3 or 4 tiles
        # ─────────────────────────────────────────────────────────────
        if len(selected_upper) == 2:
            # Get best offer per selected bank
            best_per_bank = {}
            for card in selected_offers:
                bank_upper = card.bank.upper()
                if bank_upper not in best_per_bank:
                    best_per_bank[bank_upper] = card
            
            # Get list of best offers per bank, sorted by savings
            best_selected_list = sorted(best_per_bank.values(), key=lambda c: c.savings, reverse=True)
            
            if len(best_selected_list) >= 2:
                # Both banks have offers
                if best_selected_list[0].savings == best_selected_list[1].savings:
                    # Same savings: show both (max 4 tiles)
                    best_selected_list[0].label = f"{best_selected_list[0].bank} Offer"
                    best_selected_list[1].label = f"{best_selected_list[1].bank} Offer"
                    labeled.append(best_selected_list[0])
                    labeled.append(best_selected_list[1])
                else:
                    # Different savings: show best only (max 3 tiles)
                    best_selected_list[0].label = "Best Among Selected"
                    labeled.append(best_selected_list[0])
            elif len(best_selected_list) == 1:
                # Only one selected bank has offers
                best_selected_list[0].label = "Your Card Offer"
                labeled.append(best_selected_list[0])
            
            # Add best non-selected if better savings
            if non_selected_offers:
                best_other = non_selected_offers[0]
                best_selected_savings = selected_offers[0].savings if selected_offers else 0
                if best_other.savings > best_selected_savings:
                    best_other.label = "Best Offer"
                    labeled.append(best_other)
            
            # Add best default
            if default_offers:
                default_offers[0].label = "Default Offer"
                labeled.append(default_offers[0])
            
            return labeled
        
        return labeled


class OfferEngine:
    """Main offer engine"""

    def __init__(self):
        self.base_fare_gen = BaseFareGenerator()
        self.price_strip_gen = PriceStripGenerator()
        self.discount_calc = DiscountCalculator()
        self.final_price_calc = FinalPriceCalculator()
        self.gatekeeper = AuthGatekeeper()
        self.labeler = TileLabeler()

    def generate_offer_card(
        self,
        offer: Offer,
        base_price: int,
        platform_cta: str,
        is_authenticated: bool,
    ) -> OfferCard:
        discount = self.discount_calc.calculate(offer, base_price)
        final_price, savings = self.final_price_calc.calculate(offer, base_price, discount)
        locked = (not is_authenticated) and offer.login_required
        
        # Initial label - will be updated by TileLabeler
        label = "Default Offer" if (
            offer.bank.lower() == "any" or 
            offer.offer_id.startswith("DEFAULT")
        ) else "Offer"
        
        reasons = [f"Payment: {offer.payment_method}"]
        if offer.min_txn > 0:
            reasons.append(f"Min txn: ₹{int(offer.min_txn)}")
        else:
            reasons.append("No minimum booking")
        reasons.append(f"Valid till {offer.valid_to}")
        
        return OfferCard(
            offer_id=offer.offer_id,
            label=label,
            bank=offer.bank,
            card_name=offer.card_name,
            platform=offer.platform,
            payment_method=offer.payment_method,
            category=offer.category,
            coupon_code=offer.coupon_code,
            discount_type=offer.discount_type,
            discount_value=offer.discount_value,
            max_discount=offer.max_discount,
            min_txn=offer.min_txn,
            final_price=final_price,
            savings=savings,
            locked=locked,
            reasons=reasons,
            cta_url=platform_cta,
        )

    def process_search(
        self,
        from_code: str,
        to_code: str,
        travel_date: date,
        candidates: List[Offer],
        is_authenticated: bool,
        platform_prices: Optional[Dict[str, int]] = None,
        offer_locking_enabled: bool = True,
        selected_banks: Optional[List[str]] = None,
    ) -> tuple[SearchSummary, List[PriceStripItem], List[OfferCard]]:
        """
        Process search and apply offer gating.
        
        Args:
            from_code: Origin airport
            to_code: Destination airport
            travel_date: Travel date
            candidates: Filtered offer list
            is_authenticated: User auth status
            platform_prices: Base prices per platform
            offer_locking_enabled: Feature flag for offer locking
            selected_banks: User-selected bank filters for tile labeling
        """
        # Generate price strip
        price_strip = self.price_strip_gen.generate(
            from_code, to_code, travel_date, platform_prices
        )
        
        # Get base fare from price strip
        base_fare = 0
        date_str = travel_date.isoformat()
        for item in price_strip:
            if item.date == date_str:
                base_fare = item.price
                break
        
        if base_fare == 0:
            base_fare = self.base_fare_gen.generate(from_code, to_code, travel_date)
        
        # Generate offer cards
        offer_cards = []
        for offer in candidates:
            platform_url = PLATFORM_URLS.get(offer.platform, "")
            card = self.generate_offer_card(offer, base_fare, platform_url, is_authenticated)
            offer_cards.append(card)
        
        # Sort by savings (higher first)
        offer_cards.sort(key=lambda c: (c.savings, -c.final_price), reverse=True)
        
        # Apply tile labeling based on card selection
        offer_cards = self.labeler.label_offers(offer_cards, selected_banks)
        
        # Apply auth gating with feature flag
        offer_cards = self.gatekeeper.gate_offers(
            offer_cards, is_authenticated, offer_locking_enabled
        )
        
        summary = SearchSummary(
            from_airport=from_code,
            to_airport=to_code,
            date=travel_date.isoformat(),
            base_fare=base_fare,
        )
        
        return summary, price_strip, offer_cards
