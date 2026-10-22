from decimal import Decimal
from django.conf import settings
from .models import Cart, CartItem
from Shop.models import Product, Coupon


def apply_coupon_logic(cart_total, coupon):
    """Допоміжна функція розрахунку суми знижки"""
    if not coupon or not coupon.is_valid():
        return Decimal('0.00')

    if coupon.discount_type == 'percent':
        discount = cart_total * (coupon.discount_value / Decimal('100'))
    else:
        discount = coupon.discount_value

    # Знижка не може перевищувати загальну вартість товарів
    return min(discount, cart_total)


class SessionCart:
    """Session-based кошик для анонімних користувачів"""
    
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        
        self.cart = cart
    
    def add(self, product, quantity=1, update_quantity=False):
        """Додати товар в кошик"""
        product_id = str(product.id)
        
        if product_id not in self.cart:
            self.cart[product_id] = {
                'quantity': 0,
                'price': str(product.price)
            }
        
        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        
        self.save()
    
    def save(self):
        """Зберегти зміни в сесії"""
        self.session.modified = True
    
    def remove(self, product):
        """Видалити товар з кошика"""
        product_id = str(product.id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()
    
    def __iter__(self):
        """Ітерація по товарах в кошику"""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        product_map = {str(p.id): p for p in products}
        
        for product_id, item_data in self.cart.items():
            if product_id in product_map:
                price = Decimal(item_data['price'])
                yield {
                    'product': product_map[product_id],
                    'quantity': item_data['quantity'],
                    'price': price,
                    'total_price': price * item_data['quantity'],
                }
    
    def __len__(self):
        """Підрахунок загальної кількості товарів"""
        return sum(item['quantity'] for item in self.cart.values())
    
    def get_total_price(self):
        """Загальна сума кошика без знижки"""
        return sum(
            Decimal(item['price']) * item['quantity'] 
            for item in self.cart.values()
        )
    
    def clear(self):
        """Очистити кошик з сесії без KeyError"""
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.save()

    def get_discount(self):
        """Розрахунок розміру знижки для сесійного кошика"""
        coupon_id = self.session.get('coupon_id')
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                return apply_coupon_logic(self.get_total_price(), coupon)
            except Coupon.DoesNotExist:
                pass
        return Decimal('0.00')

    def get_total_price_after_discount(self):
        """Загальна сума з урахуванням знижки"""
        return self.get_total_price() - self.get_discount()


class DatabaseCart:
    """Database-based кошик для зареєстрованих користувачів"""
    
    def __init__(self, request):
        self.request = request
        self.user = request.user
        self.cart, created = Cart.objects.get_or_create(user=self.user)
    
    def add(self, product, quantity=1, update_quantity=False):
        """Додати товар в кошик"""
        cart_item, created = CartItem.objects.get_or_create(
            cart=self.cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            if update_quantity:
                cart_item.quantity = quantity
            else:
                cart_item.quantity += quantity
            cart_item.save()
    
    def remove(self, product):
        """Видалити товар з кошика"""
        CartItem.objects.filter(
            cart=self.cart,
            product=product
        ).delete()
    
    def __iter__(self):
        """Ітерація по товарах"""
        for item in self.cart.items.select_related('product'):
            yield {
                'product': item.product,
                'quantity': item.quantity,
                'price': item.product.price,
                'total_price': item.get_total_price()
            }
    
    def __len__(self):
        """Кількість товарів"""
        return self.cart.get_total_items()
    
    def get_total_price(self):
        """Загальна сума без знижки"""
        return self.cart.get_total_price()
    
    def clear(self):
        """Очистити кошик"""
        self.cart.items.all().delete()

    def get_discount(self):
        """Розрахунок розміру знижки для кошика в БД"""
        coupon_id = self.request.session.get('coupon_id')
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id)
                return apply_coupon_logic(self.get_total_price(), coupon)
            except Coupon.DoesNotExist:
                pass
        return Decimal('0.00')

    def get_total_price_after_discount(self):
        """Загальна сума з урахуванням знижки"""
        return self.get_total_price() - self.get_discount()


def get_cart(request):
    """Фабрика для отримання правильного типу кошика"""
    if request.user.is_authenticated:
        return DatabaseCart(request)
    else:
        return SessionCart(request)


def merge_carts(request):
    """Об'єднати session cart з database cart при авторизації / реєстрації"""
    if not request.user.is_authenticated:
        return
    
    session_cart = SessionCart(request)
    db_cart = DatabaseCart(request)
    
    for item in session_cart:
        db_cart.add(
            product=item['product'],
            quantity=item['quantity'],
            update_quantity=False
        )
    
    session_cart.clear()