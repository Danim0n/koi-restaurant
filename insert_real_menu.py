import re
from backend.database import SessionLocal, engine, Base
from backend.models.menu import MenuCategory, MenuItem

# Agrupamos los platos por su categoría exacta, sin números al principio
MENU_DATA = {
    "Bandejas": {
        "description": "Sushi en bandejas variadas ideales para compartir.",
        "items": [
            {"name": "Bandeja 1 (12 Piezas)", "price": 13.50, "description": "1 Sushi Atún, 1 Sushi Salmón, 1 Sushi Gamba, 1 Pez Mantequilla, 4 Maki Atún, 4 Maki Salmón"},
            {"name": "Bandeja 2 (18 Piezas)", "price": 20.50, "description": "8 California Maki, 3 Sashimi Salmón, 3 Sashimi Atún, 1 Sushi Atún, 1 Sushi Salmón, 1 Sushi Gamba, 1 Pez Mantequilla"},
            {"name": "Bandeja 3 (17 Piezas)", "price": 24.50, "description": "3 Sushi Salmón, 2 Sushi Atún, 2 Pez Mantequilla, 2 Sushi Gambas, 8 California Roll"},
            {"name": "Bandeja 4 (24 Piezas)", "price": 28.00, "description": "2 Sashimi Atún, 2 Sashimi Salmón, 2 Sushi Salmón, 2 Sushi Atún, 4 Maki Salmón, 4 Maki Atún, 4 Salmón Uramaki, 4 Sushi Atún Uramaki"},
            {"name": "Bandeja 5 (36 Piezas)", "price": 44.00, "description": "2 Sushi Gambas, 2 Pescado Blanco, 4 Sushi Salmón, 4 Sushi Atún, 4 Maki Salmón, 4 Maki Atún, 4 Sésamo Roll, 4 Salmón Uramaki, 4 Aguacate Roll, 4 California Roll"},
            {"name": "Bandeja 6 (38 Piezas)", "price": 44.00, "description": "2 Sushi Atún, 2 Salmón, 2 Anguila, 2 Gambas, 2 Pez Mantequilla, 4 California Roll, 4 California Sésamo, 4 Atún Uramaki, 4 Salmón Uramaki, 4 Maki Atún, 4 Maki Salmón, 4 Maki Pez Mantequilla"}
        ]
    },
    "Nuevo Maki Roll": {
        "description": "Nuestras últimas e innovadoras incorporaciones de autor.",
        "items": [
            {"name": "Poké de Salmón", "price": 10.95, "description": "Base de arroz con salmón fresco, aguacate y complementos"},
            {"name": "Poké de Atún", "price": 11.95, "description": "Base de arroz con atún fresco, vegetales y salsas"},
            {"name": "Maki Panko de Salmón", "price": 11.95, "description": "Langostinos, aguacate y chutney de fruta con cobertura de salmón"},
            {"name": "Uramaki de Langostinos Panko", "price": 12.95, "description": "Langostinos panko, aguacate, atún y salmón"},
            {"name": "Uramaki de Salmón", "price": 11.95, "description": "Salmón flameado, cangrejo y pepino"},
            {"name": "Kokoro Roll", "price": 12.95, "description": "Fuet y pepino, salmón flameado y láminas de almendra tostada"},
            {"name": "Kiss me Roll", "price": 12.95, "description": "Langostinos en tempura, aguacate, salmón flameado, masago, tobiko y salsa creamy/anguila"},
            {"name": "Dragon Lovers", "price": 16.95, "description": "Combinación especial del chef en rollo dragón"},
            {"name": "Gourmet Box", "price": 27.00, "description": "Selección premium variada de rolls gourmet"},
            {"name": "Love in City Rollo", "price": 12.95, "description": "Especialidad de la casa con topping e ingredientes seleccionados"}
        ]
    },
    "Roll 8 Piezas": {
        "description": "Uramakis y rolls tradicionales de 8 piezas.",
        "items": [
            {"name": "Salmón Roll", "price": 9.95, "description": "Aguacate, salmón, sésamo y mayonesa"},
            {"name": "Gambas Roll", "price": 9.95, "description": "Gambas, pepino y aguacate envuelto en sésamo"},
            {"name": "Atún Roll", "price": 10.50, "description": "Atún, aguacate y mayonesa envuelto en sésamo"},
            {"name": "Pollo Uramaki", "price": 9.95, "description": "Pollo crujiente y aguacate cubierto de sésamo con salsa katsu"},
            {"name": "Tempura de Pollo Uramaki", "price": 10.95, "description": "Pollo en tempura crujiente en formato uramaki"},
            {"name": "Dancing Salmón Roll", "price": 9.95, "description": "Salmón y aguacate envuelto en sésamo con topping de goma wakame"},
            {"name": "Cheese Waka Roll", "price": 9.95, "description": "Aguacate, mayonesa y gambas cocidas con tobiko"},
            {"name": "Pez Mantequilla Roll", "price": 10.50, "description": "Pez mantequilla flameado con aguacate y queso envuelto en aguacate con salsa de trufa"},
            {"name": "Dinamita Roll", "price": 10.50, "description": "Gambas, aguacate y tobiko envuelto en salmón"},
            {"name": "Sake Cheese Bamboo Roll", "price": 10.50, "description": "Salmón, aguacate y queso philadelphia cubierto de aguacate"}
        ]
    },
    "Arroces y Fideos": {
        "description": "Arroces y fideos japoneses salteados al wok.",
        "items": [
            {"name": "Arroz Frito con Gambas", "price": 6.50, "description": "Arroz salteado al estilo oriental con gambas y verduras"},
            {"name": "Yasai Yakiudon", "price": 7.50, "description": "Fideos gruesos udon salteados con verduras frescas"},
            {"name": "Yasai Yakiudon con Pollo", "price": 8.00, "description": "Fideos gruesos udon salteados con verduras y pollo"},
            {"name": "Yasai Yakiudon con Mariscos", "price": 11.00, "description": "Fideos gruesos udon salteados con marisco variado"},
            {"name": "Yasai Yakisoba", "price": 7.50, "description": "Fideos finos salteados con verduras al wok"}
        ]
    },
    "Ramen": {
        "description": "Sopas de fideos tradicionales con caldos caseros intensos.",
        "items": [
            {"name": "Shoyu Ramen", "price": 9.50, "description": "Caldo tradicional a base de soja con fideos, huevo y carne"},
            {"name": "Shoyu Ramen Pato", "price": 10.50, "description": "Caldo de soja con fideos y deliciosa carne de pato"}
        ]
    },
    "Tartar y Tataki": {
        "description": "Cortes selectos y pescados crudos marinados al momento.",
        "items": [
            {"name": "Tartar Atún", "price": 13.50, "description": "Atún rojo picado y sazonado con base de aguacate"},
            {"name": "Tartar Salmón", "price": 12.50, "description": "Salmón fresco marinado con aguacate y aderezo especial"},
            {"name": "Tataki Maguro", "price": 13.95, "description": "Atún ligeramente sellado al fuego (9 Cortes)"},
            {"name": "Tataki Salmón", "price": 12.95, "description": "Salmón fresco ligeramente sellado al fuego (9 Cortes)"}
        ]
    },
    "Entrantes": {
        "description": "Aperitivos, gyozas, sopas y bocados perfectos para empezar.",
        "items": [
            {"name": "Rollitos de Langostinos (6 Piezas)", "price": 7.00, "description": "Langostinos crujientes envueltos en masa fina frita"},
            {"name": "Rollitos de Vietnam (4 Piezas)", "price": 5.50, "description": "Rollitos tradicionales vietnamitas con relleno fresco"},
            {"name": "Rollitos de Pato (4 Piezas)", "price": 6.95, "description": "Rollitos crujientes rellenos de pato desmechado y verduras"},
            {"name": "Rollito de Primavera", "price": 1.80, "description": "Clásico rollito de primavera frito con carne y verduras"},
            {"name": "Rollito Vegetal (2 Piezas)", "price": 2.95, "description": "Rollitos rellenos exclusivamente de vegetales frescos"},
            {"name": "Edamame", "price": 5.00, "description": "Vainas de soja verde hervidas con un toque de sal marina"},
            {"name": "Shao Mai (5 Piezas)", "price": 6.00, "description": "Dumplings al vapor rellenos de carne y marisco al estilo tradicional"},
            {"name": "Xiao Jiao (5 Piezas)", "price": 6.50, "description": "Dumplings al vapor con masa translúcida rellenos de gambas"},
            {"name": "Xiao Long Bao (5 Piezas)", "price": 6.00, "description": "Dumplings al vapor rellenos de carne jugosa con caldo en su interior"},
            {"name": "Xiao Long Bao A la Plancha (5 Piezas)", "price": 6.95, "description": "Dumplings Xiao Long Bao terminados a la plancha para un toque crujiente"},
            {"name": "Gyoza (6 Piezas)", "price": 5.50, "description": "Empanadillas japonesas de carne y verduras hechas a la plancha/vapor"},
            {"name": "Gyoza Vegetal (6 Piezas)", "price": 5.50, "description": "Empanadillas japonesas rellenas de una selección de verduras"},
            {"name": "Dinsum Variados (5 Piezas)", "price": 6.95, "description": "Variedad selecta de bocados de dim sum cocinados al vapor"},
            {"name": "Gyoza con Queso", "price": 10.00, "description": "Gyozas doradas cubiertas o rellenas con una capa de queso fundido"},
            {"name": "Arroz Gonhan", "price": 1.60, "description": "Bol de arroz blanco japonés cocinado al vapor al estilo tradicional"},
            {"name": "Sopa Miso", "price": 4.00, "description": "Sopa tradicional japonesa a base de pasta de miso, tofu y algas"},
            {"name": "Sopa Agripicante", "price": 5.00, "description": "Sopa clásica oriental con un equilibrio perfecto entre picante y ácido"},
            {"name": "Sopa Wantún", "price": 5.50, "description": "Caldo reconfortante acompañado de empanadillas wantún rellenas"},
            {"name": "Pan Chino (1 Unidad)", "price": 1.60, "description": "Pan dulce frito, crujiente por fuera y tierno por dentro"},
            {"name": "Bun Bao Pollo", "price": 5.50, "description": "Mollete tierno al vapor relleno de pollo marinado y vegetales"},
            {"name": "Bun Bao Pato", "price": 6.50, "description": "Mollete tierno al vapor relleno de jugoso pato con salsa especial"},
            {"name": "Bolitas de Verduras (6 Piezas)", "price": 6.00, "description": "Bocados fritos y crujientes elaborados con una mezcla de verduras"},
            {"name": "Bolitas de Pollo japonés", "price": 9.00, "description": "Trozos de pollo frito al estilo karaage acompañados de arroz y alga nori"}
        ]
    }
}

def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def insert_menu():
    # 1. Forzamos la creación limpia de las tablas en el archivo correcto antes de abrir la sesión
    print("🔨 Creando y limpiando tablas de la base de datos...")
    Base.metadata.drop_all(bind=engine)   # Borra las tablas existentes para asegurar limpieza total
    Base.metadata.create_all(bind=engine) # Las vuelve a crear completamente vacías
    
    print("⏳ Conectando a la base de datos SQLite...")
    session = SessionLocal()
    try:
        category_counter = 0
        item_counter = 0
        
        for cat_name, cat_info in MENU_DATA.items():
            cat_slug = slugify(cat_name)
            
            category = MenuCategory(
                name=cat_name,
                slug=cat_slug,
                description=cat_info["description"],
                order_index=category_counter
            )
            session.add(category)
            session.flush()
            category_counter += 1
            
            for item in cat_info["items"]:
                nuevo_plato = MenuItem(
                    category_id=category.id,
                    name=item["name"],
                    price=item["price"],
                    description=item["description"],
                    is_available=True
                )
                session.add(nuevo_plato)
                item_counter += 1
                    
        session.commit()
        print(f"✅ ¡Base de datos generada e insertada con éxito!")
        print(f"   Categorías creadas: {category_counter}")
        print(f"   Platos añadidos: {item_counter}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error al insertar datos: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    insert_menu()