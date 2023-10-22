from robocorp.tasks import task
from robocorp import browser
from playwright._impl._api_types import TimeoutError as PlaywrightTimeoutError
from RPA.HTTP import HTTP
from RPA.Tables import Tables
from RPA.PDF import PDF
from RPA.Archive import Archive

@task
def order_robots_from_RobotSpareBin():
    """
    Orders robots from RobotSpareBin Industries Inc.
    Saves the order HTML receipt as a PDF file.
    Saves the screenshot of the ordered robot.
    Embeds the screenshot of the robot to the PDF receipt.
    Creates ZIP archive of the receipts and the images.
    """
    orders = get_orders()
    open_robot_order_website()
    for order in orders:
        close_modal()
        fill_form(order)
    zip_reciepts()
        
def get_orders():
    """Download the updated orders file"""
    http = HTTP()
    http.download(url='https://robotsparebinindustries.com/orders.csv', target_file='./output/orders.csv', overwrite=True)

    tables = Tables()
    orders = tables.read_table_from_csv(path='./output/orders.csv', header=True)
    
    return orders
    
def open_robot_order_website():
    """Openns the order page of the website"""
    
    browser.configure(headless=True)

    browser.goto('https://robotsparebinindustries.com/#/robot-order')
    
def close_modal():

    page = browser.page()
    page.locator('button', has_text='Yep').click()

def fill_form(order):

    page = browser.page()
    page.locator('#head').select_option(order['Head'])
    page.locator(f'#id-body-{order["Body"]}').click()
    page.get_by_placeholder('Enter the part number for the legs').fill(order['Legs'])
    page.locator('#address').fill(order['Address'])

    page.locator('#preview').click()
    page.locator('#order').click()

    while not assert_order_sent():
        continue
    
    screenshot_path = take_robot_screenshot(order['Order number'])
    create_pdf_reciept(order['Order number'], screenshot_path)
    
    page.locator('#order-another').click()

def assert_order_sent():

    page = browser.page()
    order_sent = False

    try:
        page.wait_for_selector(selector='.alert-danger', timeout=1500)
        page.locator('#order').click()
        try:
            page.wait_for_selector(selector='.alert-success', timeout=1500)
            order_sent = True
        except PlaywrightTimeoutError:
            None

    except PlaywrightTimeoutError:
        try:
            page.wait_for_selector(selector='.alert-success', timeout=1500)
            order_sent = True
        except PlaywrightTimeoutError:
            None

    return order_sent

def take_robot_screenshot(order_number):

    screenshot_path = f'./output/created-robots/{order_number}-robot.png'
    page = browser.page()
    page.locator('#robot-preview-image').screenshot(path=screenshot_path)
    reciept_html = page.locator('#receipt').inner_html()
    
    return screenshot_path

def create_pdf_reciept(order_number, screenshot_path):

    reciept_path = f'./output/reciepts/{order_number}-reciept.pdf'

    page = browser.page()
    reciept_html = page.locator('#receipt').inner_html()
    
    pdf = PDF()
    pdf.html_to_pdf(reciept_html, reciept_path)
    
    pdf.add_files_to_pdf(files=[screenshot_path], target_document=reciept_path, append=True)
    # pdf.save_pdf(reciept_path)

def zip_reciepts():

    archive = Archive()
    archive.archive_folder_with_zip(folder='./output/reciepts', archive_name='./output/reciepts/reciepts.zip')