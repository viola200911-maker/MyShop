from .models import Category

def categories_processor(request):
    # Отримуємо головні категорії та завантажуємо їхні підкатегорії
    return {
        'main_categories': Category.objects.filter(parent=None).prefetch_related('children')
    }