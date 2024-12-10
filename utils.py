import random

def generate_dummy_products():
    return [
        {'id': i, 'thumbnail_url': 'https://via.placeholder.com/100', 'title': f'Product {i}', 'desc': f'Description {i}',
         'size_s_quant': random.randint(0, 100), 'size_m_quant': random.randint(0, 100), 'size_l_quant': random.randint(0, 100),
         'delivery_time': random.randint(1, 14), 'price': round(random.uniform(5.00, 30.00), 2)} for i in range(1, 11)
    ]
