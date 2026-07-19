"""Inicialización de la aplicación Koi con la carta completa de platos.

Crea la estructura e inyecta automáticamente:
  1. Usuario administrador (desde las variables de entorno/settings).
  2. Categorías del menú con sus descripciones[cite: 13].
  3. Toda la carta de platos reales (precios, nombres y descripciones)[cite: 13].
  4. Mesas del restaurante para la gestión de reservas[cite: 12].
"""
import re
from sqlalchemy.orm import Session

from backend.auth.jwt_handler import hash_password  # Usamos el hash de tu backend
from backend.config.settings import settings
from backend.database import Base, SessionLocal, engine
from backend.models.menu import MenuCategory, MenuItem
from backend.models.table import Table
from backend.models.user import User

# ---------------------------------------------------------------------------
# Carta Completa del Restaurante (MENU_DATA)[cite: 13]
# ---------------------------------------------------------------------------
MENU_DATA = {
    "Entrantes": {
        "description": "Gran variedad de aperitivos, dumplings y bocados tradicionales para abrir el apetito.",
        "items": [
            {"name": "Rollitos de Langostinos (6 Piezas)", "price": 7.00, "description": "Rollitos de Langostinos (6 Piezas)"},
            {"name": "Rollitos de Vietnam (4 Piezas)", "price": 5.50, "description": "Rollitos de Vietnam (4 Piezas)"},
            {"name": "Rollitos de Pato (4 Piezas)", "price": 6.95, "description": "Rollitos de Pato (4 Piezas)"},
            {"name": "Rollito de Primavera", "price": 1.80, "description": "Rollito de Primavera"},
            {"name": "Rollito Vegetal (2 Piezas)", "price": 2.95, "description": "Rollito Vegetal (2 Piezas)"},
            {"name": "Edamame", "price": 5.00, "description": "Vainas de soja verde hervidas con un toque de sal."},
            {"name": "Shao Mai (5 Piezas)", "price": 6.00, "description": "Dim sum tradicional relleno."},
            {"name": "Xiao Jiao (5 Piezas)", "price": 6.50, "description": "Dim sum relleno de gambas."},
            {"name": "Xiao Long Bao (5 Piezas)", "price": 6.00, "description": "Dumplings tradicionales con caldo interior."},
            {"name": "Xiao Long Bao A la Plancha (5 Piezas)", "price": 6.95, "description": "Xiao Long Bao A la Plancha (5 Piezas)"},
            {"name": "Gyoza (6 Piezas)", "price": 5.50, "description": "Empanadillas japonesas de carne y verduras."},
            {"name": "Gyoza Vegetal (6 Piezas)", "price": 5.50, "description": "Empanadillas japonesas rellenas de verduras."},
            {"name": "Dinsum Variados (5 Piezas)", "price": 6.95, "description": "Surtido de dumplings al vapor."},
            {"name": "Gyoza con Queso", "price": 10.00, "description": "Gyozas especiales con queso fundido."},
            {"name": "Pan Chino (1 Unidad)", "price": 1.60, "description": "Pan tierno frito tradicional."},
            {"name": "Bun Bao Pollo", "price": 5.50, "description": "Mollete tierno al vapor relleno de pollo y salsas."},
            {"name": "Bun Bao Pato", "price": 6.50, "description": "Mollete tierno al vapor relleno de pato laqueado."},
            {"name": "Bolitas de Verduras (6 Piezas)", "price": 6.00, "description": "Bolitas crujientes de verduras."},
            {"name": "Bolitas de Pollo japonés", "price": 9.00, "description": "Bocados crujientes de pollo al estilo Karaage."},
            {"name": "Bolitas de Pulpo", "price": 8.50, "description": "Takoyaki tradicional con salsas y katsuobushi."}
        ]
    },
    "Sopas": {
        "description": "Caldos tradicionales y reconfortantes preparados con recetas orientales auténticas.",
        "items": [
            {"name": "Sopa Miso", "price": 4.00, "description": "Sopa tradicional japonesa de pasta de soja, tofu y algas."},
            {"name": "Sopa Agripicante", "price": 5.00, "description": "Sopa clásica agripicante al estilo oriental."},
            {"name": "Sopa Wantún", "price": 5.50, "description": "Sopa con finas pastas rellenas de carne."}
        ]
    },
    "Ensaladas": {
        "description": "Ensaladas frescas y platos ligeros con toques e ingredientes asiáticos.",
        "items": [
            {"name": "Osaka Goma Wakame", "price": 5.50, "description": "Ensalada tradicional de algas marinas marinadas con sésamo."},
            {"name": "Ensalada de Pollo", "price": 7.50, "description": "Ensalada fresca con tiras de pollo y aderezo especial."},
            {"name": "Ensalada China", "price": 6.00, "description": "Ensalada clásica china con su característico aliño agridulce."},
            {"name": "Shrimp Salad", "price": 8.50, "description": "Ensalada fresca acompañada de gambas sazonadas."}
        ]
    },
    "Tempuras y Yakitori": {
        "description": "Frituras ligeras y crujientes al estilo japonés y brochetas tradicionales a la parrilla.",
        "items": [
            {"name": "Tempura de Langostinos (6 Piezas)", "price": 9.00, "description": "Langostinos rebozados en una fritura ligera y crujiente."},
            {"name": "Tempura de Verduras (9 Piezas)", "price": 7.00, "description": "Variedad de verduras frescas de temporada en tempura."},
            {"name": "Tempura de Pollo (8 Tiras de Pollo)", "price": 7.50, "description": "Tiras de pechuga de pollo crujientes al estilo tempura."},
            {"name": "Tempura Mixta", "price": 8.50, "description": "Combinación perfecta de langostinos y verduras en tempura."},
            {"name": "Brocheta de Salmón", "price": 7.00, "description": "Brocheta de salmón a la parrilla con salsa glaseada."},
            {"name": "Brocheta de Pollo", "price": 6.00, "description": "Brocheta tradicional de pollo (Yakitori) a la plancha."},
            {"name": "Kushiyaki Atún", "price": 7.50, "description": "Brocheta japonesa de atún fresco marcado a la parrilla."},
            {"name": "Kushiyaki Gambas", "price": 6.00, "description": "Brochetas de gambas sazonadas a la plancha."}
        ]
    },
    "Sashimi, Tartar y Tataki": {
        "description": "Platos premium de pescado crudo fresco, cortes puros y elaboraciones de autor.",
        "items": [
            {"name": "Sashimi Salmón (3 Cortes)", "price": 4.50, "description": "Finas e intensas lonchas de salmón crudo fresco."},
            {"name": "Sashimi Atún (3 Cortes)", "price": 6.00, "description": "Cortes limpios y selectos de atún rojo fresco."},
            {"name": "Sashimi de Pez Mantequilla (3 Cortes)", "price": 5.00, "description": "Delicados cortes de pez mantequilla fresco."},
            {"name": "Sashimi 9 Cortes", "price": 15.00, "description": "Variado premium con 3 cortes de Salmón, 3 de Atún y 3 de Pez Mantequilla."},
            {"name": "Tartar Atún", "price": 13.50, "description": "Atún rojo picado a cuchillo marinado con aguacate y aliño japonés."},
            {"name": "Tartar Salmón", "price": 12.50, "description": "Salmón fresco picado marinado con aguacate y aderezo especial."},
            {"name": "Tataki Maguro (9 Cortes)", "price": 13.95, "description": "Atún rojo ligeramente sellado al fuego con costra de sésamo y salsa ponzu."},
            {"name": "Tataki Salmón (9 Cortes)", "price": 12.95, "description": "Salmón fresco sellado brevemente por fuera, tierno por dentro."}
        ]
    },
    "Sushi": {
        "description": "Toda nuestra selección artística de piezas moldeadas a mano: Nigiris, Makis, Uramakis, Conos y combinaciones especiales.",
        "items": [
            {"name": "Sushi Ikura Huevas de Salmón (2 Piezas)", "price": 8.00, "description": "Nigiri especial coronado con huevas de salmón premium."},
            {"name": "Sushi Tobiko Huevas de Pez Volador (2 Piezas)", "price": 7.00, "description": "Nigiri con crujientes huevas de pez volador."},
            {"name": "Sushi Tartar de Atún (2 Piezas)", "price": 7.00, "description": "Nigiri tipo Gunkan relleno de tartar de atún picado."},
            {"name": "Sushi Tartar de Salmón (2 Piezas)", "price": 6.50, "description": "Nigiri tipo Gunkan relleno de tartar de salmón."},
            {"name": "Sushi Wakame (2 Piezas)", "price": 5.00, "description": "Nigiri Gunkan cubierto de deliciosas algas wakame."},
            {"name": "Sushi de Salmón (2 Piezas)", "price": 4.50, "description": "Clásico nigiri con una lámina de salmón fresco."},
            {"name": "Sushi de Atún (2 Piezas)", "price": 5.50, "description": "Nigiri tradicional con corte de atún rojo seleccionado."},
            {"name": "Sushi de Pez de mantequilla (2 Piezas)", "price": 4.50, "description": "Nigiri de suave pez mantequilla."},
            {"name": "Sushi de Gambas (2 Piezas)", "price": 4.50, "description": "Nigiri de gamba cocida abierta al estilo japonés."},
            {"name": "Sushi de Anguila (2 Piezas)", "price": 6.50, "description": "Nigiri de anguila tostada al fuego con salsa teriyaki."},
            {"name": "Sushi de Pulpo (2 Piezas)", "price": 5.50, "description": "Nigiri con lámina de pulpo cocido y alga nori."},
            {"name": "Surimi (2 Piezas)", "price": 4.50, "description": "Nigiri de cangrejo surimi tradicional."},
            {"name": "Sushi de Aguacate (2 Piezas)", "price": 4.00, "description": "Opción vegetariana con lámina de aguacate maduro."},
            {"name": "Maki Surimi (8 Piezas)", "price": 6.00, "description": "Rollo fino relleno de surimi de cangrejo."},
            {"name": "Maki de Atún (8 Piezas)", "price": 7.00, "description": "Rollo fino relleno de atún rojo fresco."},
            {"name": "Maki de Salmón (8 Piezas)", "price": 6.50, "description": "Rollo fino relleno de salmón fresco."},
            {"name": "Maki de Salmón y Queso (8 Piezas)", "price": 7.00, "description": "Maki relleno de salmón y cremoso queso philadelphia."},
            {"name": "Maki de Pez Mantequilla (8 Piezas)", "price": 6.00, "description": "Maki fino relleno de pez mantequilla."},
            {"name": "Maki de Anguila (8 Piezas)", "price": 7.00, "description": "Maki relleno de anguila y un toque de salsa dulce."},
            {"name": "Maki Vegetal (8 Piezas)", "price": 5.00, "description": "Maki relleno de verduras frescas crujientes."},
            {"name": "Maki Wakame Gaki Wakame (8 Piezas)", "price": 5.00, "description": "Maki relleno de algas marinadas wakame."},
            {"name": "Maki de Gambas (8 Piezas)", "price": 6.00, "description": "Maki fino relleno de gamba cocida."},
            {"name": "Futomaki de la casa (8 Piezas)", "price": 11.95, "description": "Rollo grueso especial con combinación de múltiples ingredientes de la casa."},
            {"name": "Maki Crispy Atún (8 Piezas)", "price": 8.00, "description": "Maki de atún con una cobertura exterior súper crujiente."},
            {"name": "Maki Crispy Pato (8 Piezas)", "price": 7.00, "description": "Maki crujiente relleno de sabroso pato."},
            {"name": "Maki Crispy Salmón (8 Piezas)", "price": 7.50, "description": "Maki crujiente relleno de salmón."},
            {"name": "Maki Crispy Pollo (8 Piezas)", "price": 6.50, "description": "Maki crujiente relleno de pollo."},
            {"name": "Maki Crispy Aguacate y Queso (8 Piezas)", "price": 6.00, "description": "Maki crujiente relleno de aguacate y crema de queso."},
            {"name": "Temaki de Salmón", "price": 4.50, "description": "Cono relleno de arroz, salmón fresco y aguacate."},
            {"name": "Temaki de Atún", "price": 5.00, "description": "Cono relleno de arroz y atún rojo picado."},
            {"name": "Temaki de Langostinos", "price": 4.50, "description": "Cono relleno de langostinos y lechuga fresca."},
            {"name": "Temaki de Anguila", "price": 5.00, "description": "Cono relleno de sabrosa anguila tostada y salsa teriyaki."},
            {"name": "Temaki de Pollo con Salsa Teriyaki", "price": 4.50, "description": "Cono relleno de pollo crujiente con reducción teriyaki."},
            {"name": "Temaki de Surimi", "price": 4.50, "description": "Cono tradicional relleno de surimi y aguacate."},
            {"name": "Temaki Vegetal", "price": 4.50, "description": "Cono relleno de lechuga, pepino, aguacate y queso."},
            {"name": "Temaki de Pez Mantequilla", "price": 5.00, "description": "Cono relleno de suave pez mantequilla."},
            {"name": "Vegetal de Salmón (8 Piezas)", "price": 11.50, "description": "Papel de arroz sin alga nori relleno de lechuga, arroz, salmón y aguacate."},
            {"name": "Vegetal de Atún (8 Piezas)", "price": 11.95, "description": "Papel de arroz relleno de lechuga, arroz, atún y aguacate."},
            {"name": "Vegetal de Tempura con Gambas (8 Piezas)", "price": 11.95, "description": "Rollo en papel de arroz con tempura de langostinos, aguacate y lechuga."},
            {"name": "Koi Tempura (8 Piezas)", "price": 10.95, "description": "Rollito de alga nori con arroz, salmón y queso enteramente tempurizado, con cebollino y mayonesa japonesa."},
            {"name": "Koi Party (8 Piezas)", "price": 10.95, "description": "Maki invertido relleno de surimi, pepino y aguacate, cubierto con masago y anguila tostada con teriyaki."},
            {"name": "Koi Japan (8 Piezas)", "price": 11.95, "description": "Uramaki relleno de pepino, tortilla y crema de queso, cubierto con un arcoíris de carpaccio de salmón, atún y aguacate."},
            {"name": "Koi Dragón (8 Piezas)", "price": 11.95, "description": "Maki invertido relleno de langostinos en tempura, envuelto en finas algas y servido con salsa crispy."},
            {"name": "Koi Crunch Salmón (8 Piezas)", "price": 12.95, "description": "Rollito especial sin arroz, relleno de salmón, espárragos, surimi y aguacate, frito en tempura con mayonesa japonesa."},
            {"name": "Tobiko Langostinos (8 Piezas)", "price": 10.95, "description": "Gambas, aguacate y pepino envuelto por fuera en crujientes huevas de tobiko."},
            {"name": "Tobiko Salmón (8 Piezas)", "price": 10.95, "description": "Salmón y aguacate envuelto en una capa exterior de tobiko."},
            {"name": "Tobiko Atún (8 Piezas)", "price": 11.50, "description": "Atún, aguacate y queso philadelphia envuelto en tobiko rojo."},
            {"name": "Wasabi Salmón (8 Piezas)", "price": 10.95, "description": "Salmón, queso y aguacate recubierto de huevas de tobiko con toque wasabi."},
            {"name": "Wasabi Atún (8 Piezas)", "price": 11.50, "description": "Atún, queso y aguacate recubierto de tobiko wasabi."},
            {"name": "Langostino Uramaki (8 Piezas)", "price": 11.95, "description": "Aguacate, mayonesa y tempura de langostino cubierto exteriormente con tobiko."},
            {"name": "Crazy Uramaki (8 Piezas)", "price": 11.95, "description": "Cebollino, langostino y aguacate sopleteado con salsa de anguila."},
            {"name": "Deluxe Uramaki (8 Piezas)", "price": 11.95, "description": "Rollo premium combinado: 4 piezas cubiertas de atún y 4 piezas de salmón."},
            {"name": "Tori Uramaki (8 Piezas)", "price": 11.95, "description": "Pollo frito crujiente, lechuga y mayonesa con un toque de salsa de anguila."},
            {"name": "Arcoiris Roll (8 Piezas)", "price": 11.95, "description": "Centro de surimi y aguacate completamente envuelto en finos cortes de atún, salmón y pez mantequilla."},
            {"name": "Salmón Roll (8 Piezas)", "price": 9.95, "description": "Aguacate, salmón fresco, sésamo tostado y mayonesa japonesa."},
            {"name": "Gambas Roll (8 Piezas)", "price": 9.95, "description": "Gambas cocidas, pepino y aguacate envuelto en sésamo."},
            {"name": "Atún Roll (8 Piezas)", "price": 10.50, "description": "Atún fresco, aguacate y mayonesa envuelto en lluvia de sésamo."},
            {"name": "Pollo Uramaki (8 Piezas)", "price": 9.95, "description": "Pollo crujiente y aguacate cubierto de sésamo con salsa katsu."},
            {"name": "Tempura de Pollo Uramaki (8 Piezas)", "price": 10.95, "description": "Uramaki con pollo crujiente en tempura interior y salsas japonesas."},
            {"name": "Dancing Salmón Roll (8 Piezas)", "price": 9.95, "description": "Salmón y aguacate envuelto en sésamo con topping de ensalada de alga goma wakame."},
            {"name": "Cheese Waka Roll (8 Piezas)", "price": 9.95, "description": "Aguacate, mayonesa, crema y gambas cocidas decorado con tobiko."},
            {"name": "Pez Mantequilla Roll (8 Piezas)", "price": 10.50, "description": "Pez mantequilla flameado con soplete, aguacate y queso crema con salsa de trufa negra."},
            {"name": "Dinamita Roll (8 Piezas)", "price": 10.50, "description": "Gambas, aguacate y tobiko envuelto completamente en láminas de salmón fresco."},
            {"name": "Sake Cheese Bamboo Roll (8 Piezas)", "price": 10.50, "description": "Salmón fresco, aguacate y queso philadelphia cubierto con finas láminas de aguacate exterior."},
            {"name": "Aguacate Roll (8 Piezas)", "price": 10.50, "description": "Aguacate maduro y queso philadelphia envuelto en una capa extra de aguacate."},
            {"name": "Atún Uramaki (8 Piezas)", "price": 11.95, "description": "Atún, Aguacate y Queso Philadelphia cremoso."},
            {"name": "Salmón Uramaki (8 Piezas)", "price": 10.95, "description": "Salmón, Aguacate y Queso de untar."},
            {"name": "Anguila Uramaki (8 Piezas)", "price": 11.50, "description": "Anguila caramelizada, aguacate, queso y reducción de salsa de anguila."},
            {"name": "Tempura Anguila Uramaki (8 Piezas)", "price": 12.95, "description": "Rollo con interior de tempura de anguila y aguacate con toppings crujientes."},
            {"name": "Tataki Uramaki (8 Piezas)", "price": 10.50, "description": "Atún picado especiado, aguacate y queso philadelphia envuelto en sésamo aromático."},
            {"name": "Crazy Roll (8 Piezas)", "price": 9.95, "description": "Gambas, aguacate y salsa spicy, cubierto de cebolla frita crujiente y salsa de anguila."},
            {"name": "Salmón Roll de Aguacate y Atún (8 Piezas)", "price": 12.95, "description": "Combinación equilibrada de salmón, atún fresco y aguacate suave."},
            {"name": "Salmón Roll de Aguacate (8 Piezas)", "price": 12.50, "description": "Uramaki clásico de salmón envuelto en láminas finas de aguacate."},
            {"name": "Salmón Roll de Queso Philadelphia y Aguacate (8 Piezas)", "price": 12.50, "description": "Salmón fresco con aguacate y abundante queso crema."},
            {"name": "Mango Roll (8 Piezas)", "price": 11.95, "description": "Toque tropical con mango fresco, salmón, aguacate, mayonesa y huevas de tobiko."},
            {"name": "Queso Roll (8 Piezas)", "price": 12.95, "description": "Queso, tempura de langostino crujiente, aguacate, mayonesa, surimi y tobiko de salmón."},
            {"name": "Spider Roll (8 Piezas)", "price": 11.95, "description": "Tempura de langostino gigante envuelto en aguacate con mayonesa y salsa dulce teriyaki."},
            {"name": "Crub Uramaki (8 Piezas)", "price": 12.50, "description": "Soft shell crab (cangrejo de concha blanda) rebozado y frito, envuelto en arroz con salsa crispy."},
            {"name": "Pollo Teriyaki Roll (8 Piezas)", "price": 10.95, "description": "Pechuga de pollo con salsa teriyaki y pepino, acompañada de aguacate y sésamo tostado."}
        ]
    },
    "Bandejas": {
        "description": "Surtidos y combinaciones variadas de sushi, ideales para compartir y degustar varios estilos.",
        "items": [
            {"name": "Bandeja 1 (12 Piezas)", "price": 13.50, "description": "1 Sushi de Atún, 1 Sushi de Pez Mantequilla, 1 Sushi de Salmón, 4 Maki de Atún, 1 Sushi de Gamba, 4 Maki de Salmón."},
            {"name": "Bandeja 2 (18 Piezas)", "price": 20.50, "description": "8 California Maki, 1 Sushi de Salmón, 3 Sashimi de Salmón, 1 Sushi de Gamba, 3 Sashimi de Atún, 1 Sushi de Pez Mantequilla, 1 Sushi de Atún."},
            {"name": "Bandeja 3 (17 Piezas)", "price": 24.50, "description": "3 Sushi de Salmón, 2 Sushi de Gambas, 2 Sushi de Atún, 8 California Roll, 2 Sushi de Pez Mantequilla."},
            {"name": "Bandeja 4 (24 Piezas)", "price": 28.00, "description": "2 Sashimi de Atún, 4 Maki de Salmón, 2 Sashimi de Salmón, 4 Maki de Atún, 2 Sushi de Salmón, 4 Salmón Uramaki, 2 Sushi de Atún, 4 Sushi Atún Uramaki."},
            {"name": "Bandeja 5 (36 Piezas)", "price": 44.00, "description": "2 Sushi de Gambas, 4 Maki de Atún, 2 Sushi de Pescado Blanco, 4 Sésamo Roll, 4 Sushi de Salmón, 4 Salmón Uramaki, 4 Sushi de Atún, 4 Aguacate Roll, 4 Maki de Salmón, 4 California Roll."},
            {"name": "Bandeja 6 (38 Piezas)", "price": 44.00, "description": "2 Sushi de Atún, 4 California Sésamo, 2 Sushi de Salmón, 4 Atún Uramaki, 2 Sushi de Anguila, 4 Salmón Uramaki, 2 Sushi de Gambas, 4 Maki de Atún, 2 Sushi de Pez Mantequilla, 4 Maki de Salmón, 4 California Roll, 4 Maki de Pez Mantequilla."}
        ]
    },
    "Ramen": {
        "description": "Nuestras tradicionales y reconfortantes sopas japonesas con caldos cocinados a fuego lento y fideos.",
        "items": [
            {"name": "Shoyu Ramen", "price": 9.50, "description": "Sopa de fideos en caldo tradicional aromatizado con salsa de soja premium y acompañamientos tradicionales."},
            {"name": "Shoyu Ramen Pato", "price": 10.50, "description": "Sopa ramen tradicional servida con jugosos cortes de pato laqueado de la casa."},
            {"name": "Shoyu Ramen Pollo", "price": 10.00, "description": "Sopa ramen con base de caldo shoyu acompañada de pechuga de pollo tierna."}
        ]
    },
    "Tallarines y Fideos": {
        "description": "Platos principales a base de fideos salteados al wok (Yakisoba y Yakiudon) o en sopas calientes especiales.",
        "items": [
            {"name": "Yasai Yakiudon", "price": 7.50, "description": "Fideos gruesos de arroz udon salteados con verduras frescas de temporada (Yasai)."},
            {"name": "Yasai Yakiudon con Pollo", "price": 8.00, "description": "Fideos gruesos udon salteados con verduras y dados de pollo jugoso."},
            {"name": "Yasai Yakiudon con Mariscos", "price": 11.00, "description": "Fideos gruesos udon salteados al wok con verduras y mariscos seleccionados."},
            {"name": "Yasai Yakiudon con Ternera", "price": 10.00, "description": "Fideos gruesos udon salteados con tiras de ternera y verduras."},
            {"name": "Yasai Yakisoba", "price": 7.50, "description": "Fideos finos de trigo japoneses salteados al wok con verduras frescas."},
            {"name": "Yakisoba con Verduras y Gambas", "price": 8.50, "description": "Fideos finos yakisoba salteados con verduras y gambas crujientes."},
            {"name": "Fideos de Arroz con Tres Delicias", "price": 7.00, "description": "Fideos finos de arroz salteados con la clásica combinación tres delicias."},
            {"name": "Cinta de Arroz Cantonés con Ternera", "price": 8.50, "description": "Cintas de arroz frescas estilo cantonés salteadas con ternera y verduras."},
            {"name": "Tallarines Salteados", "price": 7.00, "description": "Tallarines de trigo tradicionales salteados al wok con verduras."},
            {"name": "Cha Soba Tallarines Té Verde", "price": 8.00, "description": "Fideos finos japoneses elaborados con té verde e ingredientes orientales."},
            {"name": "Tempura Udon", "price": 10.00, "description": "Sopa caliente de fideos udon servida con una crujiente tempura de langostinos aparte."},
            {"name": "Tallarines con Ternera en Salsa de Ostras", "price": 8.50, "description": "Tallarines salteados con tiras de ternera tierna en sabrosa reducción de ostras."},
            {"name": "Pad Thai", "price": 8.50, "description": "Fideos de arroz al estilo tailandés salteados con su característica salsa agridulce y cacahuetes."},
            {"name": "Yakisoba a la Plancha", "price": 9.00, "description": "Fideos japoneses yakisoba marcados y dorados a la plancha tepan."}
        ]
    },
    "Arroz": {
        "description": "Variedad de arroces salteados aromáticos al wok y tradicionales cuencos Donburi japoneses.",
        "items": [
            {"name": "Arroz Gohan", "price": 1.60, "description": "Cuenco de arroz blanco japonés cocido al vapor, base de la cocina nipona."},
            {"name": "Arroz de la Casa en Bambú", "price": 8.50, "description": "Especialidad de arroz salteado al estilo de la casa servido en caña de bambú."},
            {"name": "Arroz con Verdura y Ternera", "price": 8.00, "description": "Arroz salteado con finas verduras picadas y láminas de ternera."},
            {"name": "Arroz con Verdura y Pollo", "price": 7.50, "description": "Arroz aromático salteado con verduras y pollo jugoso."},
            {"name": "Arroz Frito Tres Delicias", "price": 5.50, "description": "El clásico e infalible arroz frito oriental con tres delicias."},
            {"name": "Arroz Frito con Gambas", "price": 6.50, "description": "Arroz frito al wok salteado con gambas seleccionadas y verduras."},
            {"name": "Unadon", "price": 12.00, "description": "Cuenco tradicional de arroz cubierto con filetes de anguila asada y glaseada en salsa dulce."},
            {"name": "Pastel de Arroz", "price": 8.50, "description": "Pastel de arroz tradicional preparado al estilo oriental."}
        ]
    },
    "Carnes": {
        "description": "Platos calientes cocinados al wok o marcados a la plancha, elaborados a base de pollo, pato, ternera y cerdo.",
        "items": [
            {"name": "Teriyaki de Pollo", "price": 8.50, "description": "Jugosa pechuga de pollo cocinada en una clásica reducción de salsa teriyaki dulce."},
            {"name": "Pollo Crujiente al Limón", "price": 7.00, "description": "Pechuga de pollo empanada y frita, servida con una refrescante salsa de limón casera."},
            {"name": "Pollo Empanado con Almendras", "price": 8.00, "description": "Dados de pollo rebozados con una costra crujiente de almendras picadas."},
            {"name": "Pollo con Verduras", "price": 7.00, "description": "Pollo salteado al wok con una rica selección de verduras de temporada."},
            {"name": "Pollo con Bambú y Setas", "price": 7.00, "description": "Combinación clásica oriental de pollo salteado con brotes de bambú y setas chinas."},
            {"name": "Pollo Gongbao", "price": 7.00, "description": "Pollo salteado al estilo Sichuan con verduras y frutos secos (toque ligeramente picante)."},
            {"name": "Pollo Katsu", "price": 8.00, "description": "Pechuga de pollo crujiente empanada en panko, servida con mayonesa japonesa y arroz."},
            {"name": "Pato Laqueado 1/2 Pieza - 6 Crepes", "price": 12.50, "description": "Medio pato laqueado al estilo Pekín, acompañado de verduras finas y 6 crepes para enrollar."},
            {"name": "Pato Laqueado 1 Pieza - 12 Crepes", "price": 24.00, "description": "Pato laqueado entero perfectamente asado, servido con salsa dulce y 12 crepes tradicionales."},
            {"name": "Pato a la Naranja", "price": 9.95, "description": "Cortes de pato asado cubiertos por una jugosa salsa cítrica de naranja dulce."},
            {"name": "Pato con Bambú y Setas", "price": 9.95, "description": "Pato jugoso salteado al wok con setas chinas sabrosas y brotes de bambú crujiente."},
            {"name": "Pato con Almendras", "price": 11.95, "description": "Pato salteado con verduras selectas y almendras tostadas por encima."},
            {"name": "Cerdo Agridulce", "price": 7.00, "description": "Dados de cerdo fritos salteados con pimientos, piña y salsa agridulce artesanal."},
            {"name": "Tiras de Solomillo de Cerdo al Sésamo", "price": 8.50, "description": "Tiras de solomillo de cerdo cocinadas al wok con un toque de sésamo y especias."},
            {"name": "Ternera con Bambú y Setas", "price": 8.50, "description": "Tiras de ternera salteadas con brotes de bambú y setas orientales."},
            {"name": "Ternera con Pimientos", "price": 8.50, "description": "Ternera tierna salteada al wok con pimientos verdes y cebolla."},
            {"name": "Ternera con Salsa de Ostras", "price": 9.00, "description": "Especialidad de ternera salteada en una intensa y untuosa salsa de ostras."},
            {"name": "Ternera a la Plancha", "price": 10.00, "description": "Tiras de ternera sazonadas cocinadas a fuego vivo en la plancha oriental."},
            {"name": "Solomillo a la Plancha", "price": 16.00, "description": "Corte de solomillo premium cocinado a la plancha en su punto exacto con guarnición."}
        ]
    },
    "Pescados, Mariscos y Tofu": {
        "description": "Elaboraciones calientes de mariscos frescos, pescados glaseados y opciones a base de tofu.",
        "items": [
            {"name": "Gambas con Verduras", "price": 9.00, "description": "Gambas salteadas al wok con una corona de verduras frescas."},
            {"name": "Gambas Picantes", "price": 9.00, "description": "Gambas cocinadas en una salsa picante especial de la casa."},
            {"name": "Gambas con Bambú y Setas", "price": 9.00, "description": "Gambas salteadas en combinación con setas chinas y bambú aromático."},
            {"name": "Gambas al Ajillo", "price": 10.50, "description": "Gambas cocinadas con ajos dorados al estilo oriental."},
            {"name": "Gambas a la Plancha", "price": 10.50, "description": "Gambas enteras sazonadas y cocinadas directamente en la plancha."},
            {"name": "Vieiras con Gambas Salteadas", "price": 16.50, "description": "Plato premium gourmet de tiernas vieiras y gambas salteadas al wok."},
            {"name": "Vieira (Unidad)", "price": 7.95, "description": "Vieira individual seleccionada preparada a la plancha con su salsa."},
            {"name": "Calamares a la Plancha con Puerros", "price": 13.50, "description": "Calamares frescos marcados en la plancha acompañado de puerros tiernos salteados."},
            {"name": "Salmón Teriyaki", "price": 16.00, "description": "Lomo de salmón fresco a la plancha bañado en salsa teriyaki sobre base vegetal."},
            {"name": "Tofu con verduras salteadas", "price": 8.50, "description": "Dados de tofu tierno salteados al wok con verduras crujientes (Opción vegetariana)."}
        ]
    }
}

MESAS = [
    (1, 2, "Barra"),
    (2, 2, "Barra"),
    (3, 4, "Interior"),
    (4, 4, "Interior"),
    (5, 6, "Interior"),
    (6, 6, "Terraza"),
    (7, 8, "Terraza"),
    (8, 10, "Sala privada"),
]

# ---------------------------------------------------------------------------
# Lógica Auxiliar
# ---------------------------------------------------------------------------
def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '-', text).strip('-')

def base_vacia(db: Session) -> bool:
    """Comprueba si el usuario administrador no existe."""
    return db.query(User).count() == 0

def bootstrap(db: Session) -> None:
    """Inserta de manera segura el admin, categorías, platos y mesas."""
    
    # 1) Usuario administrador (Solo si no existe)[cite: 12]
    admin_exists = db.query(User).filter_by(email=settings.ADMIN_EMAIL).first()
    if not admin_exists:
        admin = User(
            email=settings.ADMIN_EMAIL,
            name=settings.ADMIN_NAME,
            hashed_password=hash_password(settings.ADMIN_PASSWORD),
            is_active=True,
            is_admin=True,
        )
        db.add(admin)
        db.flush()

    # 2) Categorías y Platos (Inyección combinada)[cite: 13]
    category_counter = 0
    item_counter = 0
    
    for cat_name, cat_info in MENU_DATA.items():
        cat_slug = slugify(cat_name)
        
        # Comprobar si la categoría ya existe por su slug
        category = db.query(MenuCategory).filter_by(slug=cat_slug).first()
        if not category:
            category = MenuCategory(
                name=cat_name,
                slug=cat_slug,
                description=cat_info["description"],
                order_index=category_counter
            )
            db.add(category)
            db.flush()  # Obtener el ID generado para enlazar platos
            category_counter += 1
            
        # Insertar los platos dentro de esta categoría si no están ya registrados
        for item in cat_info["items"]:
            item_exists = db.query(MenuItem).filter_by(name=item["name"], category_id=category.id).first()
            if not item_exists:
                nuevo_plato = MenuItem(
                    category_id=category.id,
                    name=item["name"],
                    price=item["price"],
                    description=item["description"],
                    is_available=True
                )
                db.add(nuevo_plato)
                item_counter += 1
                
    # 3) Mesas del restaurante (Solo si la tabla está vacía)[cite: 12]
    mesas_creadas = 0
    if db.query(Table).count() == 0:
        for numero, capacidad, ubicacion in MESAS:
            db.add(Table(number=numero, capacity=capacidad, location=ubicacion))
            mesas_creadas += 1

    db.commit()
    print(f"📊 Resumen del Bootstrap:")
    if category_counter > 0 or item_counter > 0:
        print(f"   -> Categorías creadas: {category_counter}")
        print(f"   -> Platos añadidos al menú: {item_counter}")
    if mesas_creadas > 0:
        print(f"   -> Mesas físicas configuradas: {mesas_creadas}")


def init_db(force: bool = False) -> None:
    """Crea las tablas estructurales y ejecuta la carga de datos."""
    Base.metadata.create_all(bind=engine)  # Genera el archivo koi.db y tablas[cite: 11, 12]
    db = SessionLocal()
    try:
        if force or base_vacia(db):
            bootstrap(db)
            print("✅ Base de datos Koi inicializada con éxito con toda la carta real.")
        else:
            print("ℹ️  La base de datos ya contiene datos estructurales. Omitiendo bootstrap.")
    except Exception as e:
        db.rollback()
        print(f"❌ Error crítico al inicializar la base de datos: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()