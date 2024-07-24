from robocorp.tasks import task
from robocorp import browser

from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive

import os

table = Tables()
pdf = PDF()

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    browser.configure(slowmo=200,)
    open_robot_order_website()
    get_orders()
    archive_receipts()
    
def close_annoying_modal(page):
    # Close pops up
    page.click("text=OK")     

def open_robot_order_website():
    # Open url
    page = browser.page()
    page.goto("https://robotsparebinindustries.com/#/robot-order")
    close_annoying_modal(page)

def screenshot_robot(order_number):
    page = browser.page()
    png_filename = f"order_receipt_{order_number}.png"
    output_directory = os.path.join(os.getcwd(), "output")
    png_path = os.path.join(output_directory, png_filename)
    screenshot = page.locator('//*[@id="robot-preview-image"]').screenshot(type="png", path=png_path)
    return png_path

def embed_screenshot_to_receipt(screenshot, pdf_file, order_number):
    new_pdf_filename = f"order_receipt_{order_number}.pdf"
    output_directory = os.path.join(os.getcwd(), "output")
    new_pdf_path = os.path.join(output_directory, new_pdf_filename)

    # Coordenadas donde quieres colocar la imagen
    # x_coordinate = 10
    # y_coordinate = 50

    # Construir la cadena con las coordenadas para la imagen
    # image_with_coordinates = f"{screenshot}:x={x_coordinate},y={y_coordinate}"

    list_of_files = [pdf_file, screenshot]
    pdf.add_files_to_pdf(files=list_of_files, target_document=new_pdf_path)

def store_receipt_as_pdf(order_number):
    page = browser.page()

    pdf_filename = f"order_receipt_{order_number}.pdf"
    output_directory = os.path.join(os.getcwd(), "output")
    pdf_path = os.path.join(output_directory, pdf_filename)

    order_receipt_html = page.locator('//*[@id="order-completion"]').inner_html()
    pdf.html_to_pdf(order_receipt_html, pdf_path)
    return pdf_path  

def fill_the_form(row):
    page = browser.page()

    # Selector de ID para seleccionar la opción de la cabeza del robot
    page.select_option("#head", row["Head"])
    # Selector XPath para seleccionar el cuerpo del robot basado en el número de cuerpo proporcionado
    selector_ratio_base = '//*[@id="id-body-'
    #Completar el selector con el número recibido en row["Body"] 
    selector_ratio = f'{selector_ratio_base}{row["Body"]}"]'
    page.click(selector_ratio)
    # Selector CSS para el campo de entrada de número de las piernas del robot. Se combinan varios atributos: type= + placeholder=.
    input_legs = page.query_selector('input.form-control[type="number"][placeholder="Enter the part number for the legs"]')
    input_legs.click()
    input_legs.type(row["Legs"])
    # Selector de ID para llenar el campo de dirección
    page.fill("#address", row["Address"])
    # Selector de texto para hacer clic en el botón de vista previa
    page.click("text=Preview")
    # Selectores de ID para los botones de orden y orden adicional
    order_button_selector = '#order'
    other_order_button_selector = '#order-another' 

    def click_order_button():
        page.click(order_button_selector)

    def click_other_order_button():
        page.click(other_order_button_selector)

    while True:
        # while True: Crea un bucle infinito que seguirá ejecutándose hasta que encuentre una instrucción break.
        click_order_button()

        # Verificar si el botón "order-another" aparece, indicando éxito
        if page.query_selector(other_order_button_selector):
            order_number = row["Order number"]
            screenshot =  screenshot_robot(order_number)
            pdf_file = store_receipt_as_pdf(order_number)
            embed_screenshot_to_receipt(screenshot, pdf_file, order_number)
            click_other_order_button()
            print("El pedido se envió correctamente y se hizo clic en 'order-another'.")
            break

        print("El intento falló, reintentando...")
    
    close_annoying_modal(page)

def get_orders():
    # Download csv file and read with table
    http = HTTP()
    http.download("https://robotsparebinindustries.com/orders.csv", overwrite=True)
    orders_to_table = table.read_table_from_csv("orders.csv", header=True)
    
    for row in orders_to_table:
        print(row)
        fill_the_form(row)

def archive_receipts():
    arch = Archive()
    arch.archive_folder_with_zip("output", "output/order_receipts.zip", include="*.pdf")