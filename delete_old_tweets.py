import os
import sys
import time
import re
from datetime import datetime
from playwright.sync_api import sync_playwright

# Configuration
USER_DATA_DIR = os.path.join(os.getcwd(), "x_chrome_profile")

def setup_playwright():
    pw = sync_playwright().start()
    context = pw.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = context.new_page()
    page.set_extra_http_headers({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    return pw, context, page

def wait_for_login(page):
    print("\n--- INICIO DE SESIÓN ---")
    print("Por favor, inicia sesión en tu cuenta de X.com en la ventana del navegador que se abrió.")
    print("Una vez que hayas iniciado sesión y veas tu inicio (Home), regresa aquí y presiona ENTER.")
    
    page.goto("https://x.com/login")
    input("Presiona ENTER aquí después de haber iniciado sesión exitosamente...")
    
    if "x.com/home" in page.url or page.locator('[data-testid="SideNav_NewTweet_Button"]').is_visible():
        print("¡Inicio de sesión detectado con éxito!")
        return True
    else:
        print("Advertencia: No se detectó la página de inicio. Continuando de todas formas...")
        return True

def delete_tweet(page, tweet_element, limit_date):
    try:
        # Check the date of the tweet first
        time_element = tweet_element.locator('time')
        if not time_element.is_visible():
            return False
            
        datetime_str = time_element.get_attribute('datetime')
        if not datetime_str:
            return False
            
        # Format of datetime is YYYY-MM-DDTHH:MM:SS.000Z
        tweet_date_str = datetime_str.split('T')[0]
        
        if tweet_date_str > limit_date:
            # Skip if the tweet is newer than the limit date
            print(f"  -> Omitiendo post de fecha {tweet_date_str} (es posterior al límite {limit_date})")
            return False
            
        print(f"  [!] Detectado tweet antiguo del {tweet_date_str} ({datetime_str}). Intentando eliminar...")

        # Click the "More" button (...) on the tweet
        more_button = tweet_element.locator('[data-testid="caret"]')
        if not more_button.is_visible():
            print("  -> No se encontró el botón de menú (...)")
            return False
        
        more_button.click()
        page.wait_for_timeout(500)
        
        # Click the "Delete" option in the dropdown menu
        delete_option = page.locator('//div[@role="menuitem"]//span[contains(text(), "Delete") or contains(text(), "Eliminar")]')
        if not delete_option.is_visible():
            print("  -> Opción 'Eliminar' no visible en el menú")
            page.mouse.click(10, 10)
            return False
            
        delete_option.click()
        page.wait_for_timeout(500)
        
        # Confirm deletion in the confirmation dialog
        confirm_button = page.locator('[data-testid="confirmationSheetConfirm"]')
        if confirm_button.is_visible():
            confirm_button.click()
            print("  [✓] Tweet eliminado con éxito.")
            page.wait_for_timeout(1500) # Wait for UI to update
            return True
    except Exception as e:
        print(f"Error al procesar/eliminar tweet: {e}")
        try:
            page.mouse.click(10, 10)
        except:
            pass
    return False

def delete_via_profile(page, username, limit_date):
    profile_url = f"https://x.com/{username}"
    print(f"\nNavegando directamente al perfil: {profile_url}")
    page.goto(profile_url)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(5000)
    
    deleted_count = 0
    
    while True:
        tweets = page.locator('article[data-testid="tweet"]').all()
        print(f"\nSe encontraron {len(tweets)} tweets en pantalla.")
        
        if not tweets:
            print("No hay tweets en pantalla. Desplazando hacia abajo para cargar...")
            page.keyboard.press("PageDown")
            page.wait_for_timeout(3000)
            continue
            
        deleted_in_loop = 0
        
        for idx, tweet in enumerate(tweets, 1):
            # Check if this tweet is by the target user (case-insensitive check for href)
            user_link = tweet.locator(f'a[href="/{username}" i]').first
            
            if user_link.is_visible():
                if delete_tweet(page, tweet, limit_date):
                    deleted_count += 1
                    deleted_in_loop += 1
                    time.sleep(1.5)
                    break # Break to refresh tweets list because DOM changed
            else:
                print(f"  -> Tweet #{idx} omitido: no parece ser un post propio (puede ser un retweet o anuncio)")
        
        if deleted_in_loop == 0:
            print("Desplazando hacia abajo para cargar tweets más antiguos...")
            page.keyboard.press("PageDown")
            page.wait_for_timeout(2500)

    print(f"\nProceso terminado. Total de tweets eliminados: {deleted_count}")

def main():
    print("====================================================")
    print("  X.com (Twitter) Old Tweets Deleter (Playwright)   ")
    print("====================================================")
    
    username = input("Introduce tu usuario de X (ej. megashopmx): ").strip().replace("@", "")
    if not username:
        print("El usuario no puede estar vacío.")
        sys.exit(1)
        
    while True:
        limit_date = input("Introduce la fecha límite (AAAA-MM-DD) para borrar posts de ese día y anteriores: ").strip()
        try:
            # Validate date format
            datetime.strptime(limit_date, "%Y-%m-%d")
            break
        except ValueError:
            print("Formato de fecha inválido. Por favor, usa el formato AAAA-MM-DD (ej: 2015-12-31).")
            
    print(f"\nSe buscarán y borrarán los tweets de @{username} del {limit_date} y anteriores.")
    
    pw, context, page = setup_playwright()
    
    try:
        page.goto("https://x.com/home")
        page.wait_for_timeout(2000)
        
        if not page.locator('[data-testid="SideNav_NewTweet_Button"]').is_visible():
            wait_for_login(page)
            
        delete_via_profile(page, username, limit_date)
        
    except KeyboardInterrupt:
        print("\nProceso interrumpido por el usuario.")
    finally:
        context.close()
        pw.stop()

if __name__ == "__main__":
    main()
