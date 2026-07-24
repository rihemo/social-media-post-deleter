import os
import sys
import time
import json
import re
from playwright.sync_api import sync_playwright

# Configuration
USERNAME = "megashopmx"
UNTIL_DATE = "2016-01-01"  # Deletes tweets BEFORE this date (2015 and older)
USER_DATA_DIR = os.path.join(os.getcwd(), "x_chrome_profile")

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

def wait_for_login(page):
    print("\n--- INICIO DE SESIÓN ---")
    print("Por favor, inicia sesión en tu cuenta de X.com en la ventana del navegador que se abrió.")
    print("Una vez que hayas iniciado sesión y veas tu inicio (Home), regresa aquí y presiona ENTER.")
    
    page.goto("https://x.com/login")
    input("Presiona ENTER aquí después de haber iniciado sesión exitosamente...")
    
    # Verify login by checking cookies or looking for home elements
    if "x.com/home" in page.url or page.locator('[data-testid="SideNav_NewTweet_Button"]').is_visible():
        print("¡Inicio de sesión detectado con éxito!")
        return True
    else:
        print("Advertencia: No se detectó la página de inicio. Continuando de todas formas...")
        return True

def delete_tweet(page, tweet_element):
    try:
        # Check the date of the tweet first
        time_element = tweet_element.locator('time')
        if not time_element.is_visible():
            # If it's a retweet or has no time element visible yet
            return False
            
        datetime_str = time_element.get_attribute('datetime')
        if not datetime_str:
            return False
            
        tweet_year = int(datetime_str.split('-')[0])
        
        if tweet_year > 2015:
            # Skip if the tweet is newer than 2015
            print(f"  -> Omitiendo post del año {tweet_year} (es más reciente que 2015)")
            return False
            
        print(f"  [!] Detectado tweet antiguo de {tweet_year} ({datetime_str}). Intentando eliminar...")

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

def delete_via_profile(page):
    profile_url = f"https://x.com/{USERNAME}"
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
            # Check if this tweet is by megashopmx (case-insensitive check for href)
            # Match href exactly "/megashopmx" case-insensitive
            user_link = tweet.locator(f'a[href="/{USERNAME}" i]').first
            
            if user_link.is_visible():
                if delete_tweet(page, tweet):
                    deleted_count += 1
                    deleted_in_loop += 1
                    time.sleep(1.5)
                    break # Break the loop to reload elements and avoid stale elements
            else:
                # Might be a retweet or ad
                print(f"  -> Tweet #{idx} omitido: no parece ser un post propio (puede ser un retweet o anuncio)")
        
        if deleted_in_loop == 0:
            print("Desplazando hacia abajo para cargar tweets más antiguos...")
            page.keyboard.press("PageDown")
            page.wait_for_timeout(2500)

    print(f"\nProceso terminado. Total de tweets eliminados: {deleted_count}")

def delete_via_search(page):
    # Construct search query for tweets before 2016-01-01
    search_query = f"from:{USERNAME} until:{UNTIL_DATE}"
    encoded_query = search_query.replace(":", "%3A").replace(" ", "%20")
    search_url = f"https://x.com/search?q={encoded_query}&f=live"
    
    print(f"\nNavegando a la búsqueda: {search_query}")
    page.goto(search_url)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(4000)
    
    # Check if there are no results page
    no_results = page.locator('//span[contains(text(), "No hay resultados") or contains(text(), "No results")]').is_visible()
    if no_results:
        print("La búsqueda no devolvió resultados (puede deberse a que la cuenta es privada).")
        print("Cambiando a modo de eliminación directa desde el perfil...")
        delete_via_profile(page)
        return

    deleted_count = 0
    no_tweets_attempts = 0
    
    while True:
        # Locate all tweet articles currently loaded on the page
        tweets = page.locator('article[data-testid="tweet"]').all()
        
        if not tweets:
            print("No se encontraron más tweets. Desplazando hacia abajo...")
            page.keyboard.press("PageDown")
            page.wait_for_timeout(2000)
            no_tweets_attempts += 1
            if no_tweets_attempts > 5:
                print("No se encontraron más tweets después de varios intentos. Proceso finalizado.")
                break
            continue
            
        no_tweets_attempts = 0
        deleted_in_loop = 0
        
        for tweet in tweets:
            # Check if this tweet is indeed by our target user (avoiding ads or glitches)
            user_link = tweet.locator(f'a[href="/{USERNAME}"]').first
            if user_link.is_visible():
                if delete_tweet(page, tweet):
                    deleted_count += 1
                    deleted_in_loop += 1
                    # Small random delay to look more human
                    time.sleep(1.5)
                    break # Break out of loop to refresh the tweets locator list since DOM changed
        
        if deleted_in_loop == 0:
            # If we didn't delete anything in this view, scroll down to load older ones
            print("No se eliminaron tweets en esta vista. Desplazando hacia abajo...")
            page.keyboard.press("PageDown")
            page.wait_for_timeout(2000)

    print(f"\nProceso terminado. Total de tweets eliminados: {deleted_count}")

def main():
    print("====================================================")
    print("  X.com (Twitter) Old Tweets Deleter (Playwright)   ")
    print("====================================================")
    
    pw, context, page = setup_playwright()
    
    try:
        # Check if we already have session cookies saved, otherwise log in
        page.goto("https://x.com/home")
        page.wait_for_timeout(2000)
        
        if not page.locator('[data-testid="SideNav_NewTweet_Button"]').is_visible():
            wait_for_login(page)
            
        delete_via_profile(page)
        
    except KeyboardInterrupt:
        print("\nProceso interrumpido por el usuario.")
    finally:
        context.close()
        pw.stop()

if __name__ == "__main__":
    main()
