import re, logging, os, asyncio, time
from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page, expect
class Class_Checker:
    def __init__(self, credentials):
        self.credentials = credentials

    async def run(self, classes):
        async with async_playwright() as playwright:
            chromium = playwright.chromium
            browser = await chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            await self.login(page)
            tasks = [asyncio.create_task(self.find(context, _class['course_subject'], _class['course_number'], _class['section_number'])) for _class in classes.values()]
            result = await asyncio.gather(tasks)
            print(result)

            #TODO - process result into original classes

    async def login(self, page: Page):
        try:
            await page.goto("https://prod.ps.stonybrook.edu/psp/csprods/?cmd=login")
            username_field = page.get_by_label('Stony Brook ID#')
            password_field = page.get_by_label('Password')
            submit_form = page.locator('input[name=Submit]')
            await username_field.fill(self.credentials['SOLAR_ID'])
            await password_field.fill(self.credentials['SOLAR_PWD'])
            await submit_form.click()
            
            await expect(page).to_have_title('Employee-facing registry content')
        except Exception as error:
            logging.critical(error)
            self.quit()

    # Check the target course on SOLAR and return the (current status, instructor_name)
    async def find(self, context, course_subject, course_number, section_number):
        logging.debug(f"LOOKING FOR {course_subject} {course_number} [{section_number}]")

        try:
            page = await context.new_page()
            await page.goto("https://prod.ps.stonybrook.edu/psp/csprods/EMPLOYEE/CAMP/c/SA_LEARNER_SERVICES.CLASS_SEARCH.GBL?1&PORTALPARAM_PTCNAV=SU_CLASS_SEARCH&EOPP.SCNode=CAMP&EOPP.SCPortal=EMPLOYEE&EOPP.SCName=ADMN_SOLAR_SYSTEM&EOPP.SCLabel=Enrollment&EOPP.SCFName=HCCC_ENROLLMENT&EOPP.SCSecondary=true&EOPP.SCPTcname=PT_PTPP_SCFNAV_BASEPAGE_SCR&FolderPath=PORTAL_ROOT_OBJECT.CO_EMPLOYEE_SELF_SERVICE.SU_STUDENT_FOLDER.HCCC_ENROLLMENT.SU_CLASS_SEARCH&IsFolder=false")
            await expect(page).to_have_title('Class Search')

            #Choose current semester
            iframe = page.frame_locator('#ptifrmtgtframe')
            term_select_field = iframe.get_by_label('Term')
            await term_select_field.select_option('Spring 2024')
            time.sleep(0.5)
            
            #Fill course subject
            subject_field = iframe.get_by_label('Subject')
            await subject_field.fill(course_subject)

            #Fill course number
            course_number_field = iframe.get_by_label('Course Number')
            await course_number_field.click() #to reflect the change
            time.sleep(0.5)
            await course_number_field.fill(course_number)

            #Fill undergraduate
            course_career_field = iframe.get_by_label('Course Career')
            await course_career_field.select_option('Undergraduate')
            time.sleep(0.5)

            #Click off to see all course
            open_class_only_button = iframe.get_by_label('Show Open Classes Only')
            await open_class_only_button.click()

            #Search
            submit_form = iframe.get_by_role('button', name='Search', exact=True)
            await submit_form.click()

            course_status = await iframe.locator(f"//*[contains(text(),'{section_number}')]/../../../../td[position() = (last() - 1)]/div/div/img").get_attribute('alt')
            course_instructor = await iframe.locator(f"//*[contains(text(),'{section_number}')]/../../../../td[position() = (last() - 3)]/div/span").inner_text()

            return (course_status.upper(), course_instructor)

        except Exception as error:
            logging.critical(error)

if __name__ == '__main__':
    async def main():
        load_dotenv()
        CREDENTIALS = {
            'SOLAR_ID': os.getenv('SOLAR_ID'),
            'SOLAR_PWD': os.getenv('SOLAR_PWD')
        }
        classes = {
            "11111111": {
                'course_subject': 'CSE',
                'course_number': 300,
                'section_number': '50494'
            },
            "22222222": {
                'course_subject': 'CSE',
                'course_number': 312,
                'section_number': '50712'
            }
        }
        class_checker = Class_Checker(CREDENTIALS)
        await class_checker.run(classes=classes)

    asyncio.run(main())