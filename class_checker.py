import re, logging, os, asyncio
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, expect
class Class_Checker:
    def __init__(self, credentials):
        self.credentials = credentials

    async def run(self, classes):
        async with async_playwright() as playwright:
            chromium = playwright.chromium
            browser = await chromium.launch(headless=False)
            page = await browser.new_page()
            await self.login(page)
            for _class in classes:
                await self.find(_class['course_subject'], _class['course_number'], _class['section_number'])

    async def login(self, page: Page):
        try:
            await page.goto("https://prod.ps.stonybrook.edu/psp/csprods/?cmd=login")
            username_field = page.get_by_label('Stony Brook ID#')
            password_field = page.get_by_label('Password')
            submit_form = page.locator('input[name=Submit]')
            await username_field.fill(self.credentials['SOLAR_ID'])
            await password_field.fill(self.credentials['SOLAR_PWD'])
            await submit_form.click()
            
            await expect(page).to_have_title('Class Search')
        except Exception as error:
            logging.critical(error)
            self.quit()

    # Check the target course on SOLAR and return the (current status, instructor_name)
    async def find(self, course_subject, course_number, section_number):
        logging.debug(f"LOOKING FOR {course_subject} {course_number} [{section_number}]")

        try:
            self.driver.get("https://psns.cc.stonybrook.edu/psp/csprods/EMPLOYEE/CAMP/c/SA_LEARNER_SERVICES.CLASS_SEARCH.GBL?1&PORTALPARAM_PTCNAV=SU_CLASS_SEARCH&EOPP.SCNode=CAMP&EOPP.SCPortal=EMPLOYEE&EOPP.SCName=ADMN_SOLAR_SYSTEM&EOPP.SCLabel=Enrollment&EOPP.SCFName=HCCC_ENROLLMENT&EOPP.SCSecondary=true&EOPP.SCPTcname=PT_PTPP_SCFNAV_BASEPAGE_SCR&FolderPath=PORTAL_ROOT_OBJECT.CO_EMPLOYEE_SELF_SERVICE.SU_STUDENT_FOLDER.HCCC_ENROLLMENT.SU_CLASS_SEARCH&IsFolder=false")
            iframe = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[1]/iframe'))
            )
            self.driver.switch_to.frame(iframe)
            term_select_field = Select(WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "CLASS_SRCH_WRK2_STRM$35$"))
            ))
            term_select_field.select_by_value("1244") #SELECT SPRING 2024
            time.sleep(0.5)
            
            subject_field = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "SSR_CLSRCH_WRK_SUBJECT$0"))
            )
            subject_field.send_keys(course_subject)

            course_number_field = self.driver.find_element(By.ID, "SSR_CLSRCH_WRK_CATALOG_NBR$1")
            course_number_field.click()
            time.sleep(0.5)
            course_number_field.send_keys(course_number)

            course_career_field = Select(WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.ID, "SSR_CLSRCH_WRK_ACAD_CAREER$2"))
            ))
            course_career_field.select_by_value('UGRD')
            time.sleep(0.5)

            open_class_only_button = self.driver.find_element(By.ID, 'SSR_CLSRCH_WRK_SSR_OPEN_ONLY$3')
            open_class_only_button.click()

            submit_form = self.driver.find_element(By.ID, 'CLASS_SRCH_WRK2_SSR_PB_CLASS_SRCH')
            submit_form.click()

            course_status = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(),'{section_number}')]/../../../../td[position() = (last() - 1)]/div/div/img"))
            )
            course_instructor = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, f"//*[contains(text(),'{section_number}')]/../../../../td[position() = (last() - 3)]/div/span"))
            )

            return (course_status.get_attribute('alt').upper(), course_instructor.text)

        except Exception as error:
            logging.critical(error)
            self.quit()

    def quit(self):
        self.driver.quit()


if __name__ == '__main__':
    async def main():
        load_dotenv()
        CREDENTIALS = {
            'SOLAR_ID': os.getenv('SOLAR_ID'),
            'SOLAR_PWD': os.getenv('SOLAR_PWD')
        }
        class_checker = Class_Checker(CREDENTIALS)
        await class_checker.run(classes=[])

    asyncio.run(main())