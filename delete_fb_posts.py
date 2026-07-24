import os
import sys
import time
from playwright.sync_api import sync_playwright

# Configuration
USER_DATA_DIR = os.path.join(os.getcwd(), "fb_chrome_profile")

def setup_playwright():
    pw = sync_playwright().start()
    # Launch browser with a persistent context to save login session
    context = pw.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = context.new_page()
    # Set a normal user agent to reduce bot detection
    page.set_extra_http_headers({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    return pw, context, page

def wait_for_setup(page, limit_year):
    print("\n====================================================")
    print("  INSTRUCCIONES DE PREPARACIÓN (LEER CON CUIDADO)   ")
    print("====================================================")
    print("1. En la ventana del navegador que se abrió, inicia sesión en Facebook.")
    print("2. Ve al Registro de Actividad de tu cuenta.")
    print("   El script intentará navegar automáticamente a: https://www.facebook.com/me/allactivity")
    print("3. Una vez allí, aplica los filtros manualmente:")
    print("   - Haz clic en 'Filtros' (Filters).")
    print(f"   - Selecciona el año '{limit_year}' y anteriores.")
    print("   - Selecciona la categoría 'Tus publicaciones' (o la que desees borrar).")
    print("4. Asegúrate de tener la lista de publicaciones en pantalla.")
    print("5. Regresa a esta terminal y presiona ENTER para iniciar la eliminación.")
    print("====================================================\n")
    
    page.goto("https://www.facebook.com/me/allactivity")
    input("PRESIONA ENTER AQUÍ UNA VEZ QUE HAYAS APLICADO LOS FILTROS Y VEAS LA LISTA EN PANTALLA...")

def find_action_menu_buttons(page):
    # Try different common selectors for the "..." action button in Facebook Activity Log
    # In Spanish Facebook, it often has aria-label starting with "Acciones" or "Acciones de..."
    # or it's a div with role="button" and aria-haspopup="menu"
    selectors = [
        'div[role="button"][aria-label*="Acción" i]',
        'div[role="button"][aria-label*="acción" i]',
        'div[role="button"][aria-label*="Opciones" i]',
        'div[role="button"][aria-haspopup="menu"]',
        'button[aria-label*="Acción" i]',
        'button[aria-haspopup="menu"]'
    ]
    
    for selector in selectors:
        buttons = page.locator(selector).all()
        # Filter out buttons that are not visible or are part of the main navigation/header
        visible_buttons = [b for b in buttons if b.is_visible()]
        if visible_buttons:
            # We skip the very first few if they are global buttons (like filters, activity history headers)
            # Usually activity items' menus are nested inside the main content area
            return visible_buttons
            
    return []

def delete_item(page, button):
    try:
        # Click the "..." button to open the menu
        button.scroll_into_view_if_needed()
        button.click()
        page.wait_for_timeout(1000)
        
        # Look for "Mover a la papelera" (Move to trash) or "Eliminar" (Delete)
        # We search case-insensitively for these Spanish terms
        options = page.locator('div[role="menuitem"] span').all()
        target_option = None
        
        for opt in options:
            if opt.is_visible():
                text = opt.text_content()
                if text and ("papelera" in text.lower() or "eliminar" in text.lower()):
                    target_option = opt
                    print(f"  -> Encontrada opción de menú: '{text}'")
                    break
                    
        if not target_option:
            # Click outside to close menu if no target option is found
            page.mouse.click(10, 10)
            return False
            
        target_option.click()
        page.wait_for_timeout(1500)
        
        # Confirm dialog: usually has a blue button saying "Mover a la papelera", "Mover", or "Eliminar"
        # Let's search for buttons inside the dialog
        dialog = page.locator('div[role="dialog"]')
        if dialog.is_visible():
            confirm_buttons = dialog.locator('div[role="button"], button').all()
            for btn in confirm_buttons:
                btn_text = btn.text_content()
                if btn_text and any(word in btn_text.lower() for word in ["mover", "eliminar", "confirmar", "aceptar"]):
                    print(f"  -> Confirmando acción en diálogo ('{btn_text}')")
                    btn.click()
                    page.wait_for_timeout(2000)
                    return True
                    
            # Fallback confirm by pressing Enter key if button is focused or clicking primary
            page.keyboard.press("Enter")
            page.wait_for_timeout(2000)
            return True
            
    except Exception as e:
        print(f"Error al intentar eliminar el elemento: {e}")
        try:
            page.mouse.click(10, 10) # Reset UI
        except:
            pass
    return False

def main():
    print("====================================================")
    print("  Facebook Activity Log Deleter (Playwright)        ")
    print("====================================================")
    
    limit_year = input("Introduce el año límite (ej: 2015) para borrar publicaciones de ese año y anteriores: ").strip()
    if not limit_year:
        limit_year = "2015"
        
    pw, context, page = setup_playwright()
    
    try:
        wait_for_setup(page, limit_year)
        
        deleted_count = 0
        consecutive_failures = 0
        
        print(f"\nIniciando proceso de eliminación automática para posts del {limit_year} y anteriores...")
        
        while True:
            buttons = find_action_menu_buttons(page)
            print(f"Se encontraron {len(buttons)} elementos listados con menú de acciones.")
            
            if not buttons:
                print("No se encontraron más elementos. Desplazando hacia abajo...")
                page.keyboard.press("PageDown")
                page.wait_for_timeout(3000)
                consecutive_failures += 1
                if consecutive_failures > 5:
                    print("No se detectan más elementos tras varios intentos. Proceso pausado o finalizado.")
                    break
                continue
                
            consecutive_failures = 0
            success = False
            
            # Start deleting from the first item found
            for btn in buttons:
                # To avoid clicking header buttons, we ensure the button is within the activity feed list
                # Usually we can just try to click it, and delete_item handles validation
                if delete_item(page, btn):
                    deleted_count += 1
                    success = True
                    # Random human-like delay to prevent Facebook bot blocks
                    time.sleep(2.0)
                    break # Break out of loop to reload items since DOM changed
            
            if not success:
                print("No se pudo eliminar el primer elemento en pantalla. Desplazando un poco...")
                page.keyboard.press("PageDown")
                page.wait_for_timeout(2000)
                
    except KeyboardInterrupt:
        print("\nProceso interrumpido por el usuario.")
    finally:
        print(f"\nProceso finalizado. Total de elementos eliminados/enviados a papelera: {deleted_count}")
        context.close()
        pw.stop()

if __name__ == "__main__":
    main()
