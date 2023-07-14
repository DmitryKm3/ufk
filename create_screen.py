from selenium import webdriver
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.by import By

def create_screen(notavailable,path):
    #БОЛЕЕ ЧАСА
    # Создание объекта опций
    options = webdriver.ChromeOptions()
    # Установка опции для запуска без графического интерфейса
    options.add_argument('--headless')

    i = 0
    driver = webdriver.Chrome(options=options) 
    for screen in notavailable:
        i += 1
        print("{} {}".format(i,screen))
        try:      
        
            driver.get(screen[1])
            body_element = driver.find_element(By.TAG_NAME, "html")
            driver.set_window_size(body_element.size['width'], body_element.size['height'])
            path_screen = path + "/" + str(screen[0]) + ".png"
            print(path_screen)
            driver.save_screenshot(path_screen)

        except WebDriverException: #я так понял что сайты распознают selenium и не дают доступа. 
            body_element = driver.find_element(By.TAG_NAME, "html")
            driver.set_window_size(body_element.size['width'], body_element.size['height'])
            path_screen_with_error = path + "/" + str(screen[0]) + "_with_error.png"
            print(path_screen_with_error)
            driver.save_screenshot(path_screen_with_error)
    
    driver.quit()
