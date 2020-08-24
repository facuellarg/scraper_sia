import requests
import selenium
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
# from webdriver_manager.firefox import GeckoDriverManager
from palettable.cartocolors.qualitative import Bold_10
import os
from os import path
# from palettable.lightbartlein.diverging import RedYellowBlue_11
import time
import json
import re
import argparse
import random
import threading
#------para simulacion----------------
from data_schedule import schedulers
import time
#-------------------------------------



def list_of_files(directory_path):
    return {f:True for f in os.listdir(directory_path) if path.isfile(path.join(directory_path, f)) }

def clear_hour(hour):
    hour = hour.replace('H','')
    hour=re.sub(r'\s+',' ', hour, re.I|re.A)
    hour = hour.strip()
    hour = hour.split('-')
    return [h.strip() for h in hour]

def clear_classroom(room):
    return room.split('-')

def clear_group(group):
    group=group.replace(' ','')
    return re.findall(r'\((\d+)\)',group)[0]

def login_sia(driver, user, password):
    input_user = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH,'//input[@name="username"]'))
    )
    input_pass = driver.find_element(By.XPATH, '//input[@name="password"]')
    input_user.send_keys(user)

    input_pass.send_keys(password)
    boton = driver.find_element(By.XPATH,'//input[@name="submit"]')
    boton.click()
    return True

def go_to_horario(driver):
    try:
        apoyo_academcio = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.XPATH,'//td[@title="Apoyo Académico"]'))
        )
        apoyo_academcio.click()
    except:
        return False
    mi_horario = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH,'//a[@title="Mi horario"]'))
    )
    mi_horario.click()
    return True


def go_to_list(driver,sleep_time=0):
    time.sleep(1)
    siguiente = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH,'//div[@title="Siguiente"]//a'))
    )
    siguiente.click()
    time.sleep(5)
    lista = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH,'//div[@title="Lista"]'))
    )
    lista.click()
    return True



def update_course(old_course, new_course):
    for k in new_course.keys():
        if new_course[k] is None:
            continue
        old_course[k]=new_course[k]
    return old_course

def random_color(colors):
    index =  random.randint(0,len(colors)-1)
    return colors.pop(index)

def get_scheduler_info(user,password):
    login_url='https://sia.unal.edu.co/ServiciosApp'
    HOUR = 2
    CLASSROOM = 3
    GROUP=10
    PROFESSOR = 11
    colors = Bold_10.hex_colors
    # --------------------------- para heroku-----------------------------------------------------------------
    op = webdriver.ChromeOptions()
    op.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    op.add_argument("--headless")
    op.add_argument("--disable-dev-shm-usage")
    op.add_argument("--no-sandbox")
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"),chrome_options=op)
    # -------------------------------------------------------------------------------------------------------
    # ---------------------------- para local-----------------------------------------------------------------
    # driver = webdriver.Chrome(ChromeDriverManager().install())
    # driver.minimize_window()
    # -------------------------------------------------------------------------------------------------------
    driver.get(login_url)
    print(driver)
    login_sia(driver, user, password)
    if go_to_horario(driver):
        # if user in schedulers.keys():
        #     return schedulers[user]
        go_to_list(driver)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH,'//tr[contains(@class,"af_calendar_list-row")]'))
        )
        info_courses={}
        courses_len = len(driver.find_elements(By.XPATH,'//tr[contains(@class,"af_calendar_list-row")]'))
        current_day = ""
        i = 0
        while i < courses_len:
            load = False
            tries = 0
            while not load:
                tries +=1
                if tries > 5:
                    # print(i)
                    driver.refresh()
                    go_to_horario(driver)
                    go_to_list(driver,1)
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.XPATH,'//tr[contains(@class,"af_calendar_list-row")]'))
                    )
                    tries = 0
                    continue
                courses = driver.find_elements(By.XPATH,'//tr[contains(@class,"af_calendar_list-row")]')
                # print("i antes de asignar course",i)
                course = courses[i]
                day = course.find_elements(By.XPATH,'.//th[@class="af_calendar_list-day-of-week-column af_calendar_list-cell"]')
                if len(day) !=0:
                    current_day = day[0].text.strip()

                courses = driver.find_elements(By.XPATH,'//a[contains(@class,"af_calendar_list-title-link")]')
                course = courses[i]
                course.click()

                time.sleep(2)
                container = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH,'//div[@data-afr-fid="f1"]'))
                )
                name =None
                try:
                    name = container.find_element(By.XPATH,'.//div[@class="af_dialog_title"]')
                except:
                    continue
                if name!= None:
                    spans = container.find_elements(By.XPATH, './/td[@class="af_dialog_content"]//span')
                    #i = 0
                    professor = None
                    if len(spans)>11:
                        professor = spans[PROFESSOR].text
                    hour = clear_hour(spans[HOUR].text)
                    classroom = clear_classroom(spans[CLASSROOM].text)
                    group = clear_group(spans[GROUP].text)
                    name_splited = name.text.split(' ')
                    code = name_splited[0]
                    name_course = ' '.join(name_splited[1:])
                    info_course =   {'name':name_course,
                                    'hour':hour,
                                    'group':group,
                                    'classroom':classroom,
                                    'professor':professor}
                    if code not in info_courses.keys():
                        info_courses[code]={}
                        info_courses[code]['color'] = random_color(colors)
                    if current_day in info_courses[code].keys():
                        info_courses[code][current_day] = update_course( info_courses[code][current_day],info_course)
                    else:
                        info_courses[code][current_day]=info_course
                button = WebDriverWait(container,20).until(
                    EC.presence_of_element_located((By.XPATH, '//button[@class="af_dialog_footer-button-affirmative af_dialog_footer-button p_AFTextOnly"]'))
                )
                try:
                    button.click()
                except:
                    continue
                load = True
                i += 1
        driver.quit()
        # schedulers[user]=info_courses
        return info_courses
    return("Usuario o contraseña invalidos")

def get_scheduler_info_simulation(user,password):
    time.sleep(random.randint(0,30))
    if user in schedulers.keys():
        return schedulers[user]
    else:
        return ("Usuario o contraseña invalidos")
    raise Exception("No existe el usuario")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-u','--user',help="Su usuario unal",type=str)
    parser.add_argument('-p','--password', help='Su contraseña', type=str)
    args = parser.parse_args()
    with open('./horario.json','w') as f:
        json.dump(get_scheduler_info(args.user, args.password),f,indent=2)