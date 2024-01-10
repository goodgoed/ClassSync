class Class_Record:
    def __init__(self, course_subject, course_number, section_number, target_status = ["OPEN"]):
        self.section_number = section_number
        self.course_subject = course_subject
        self.course_number = course_number
        self.instructor = ""
        self.target_status = target_status
        self.status = "UNAVAILABLE"
    def __str__(self):
        return f"[{self.section_number}] {self.course_subject} {self.course_number} - {self.instructor} | {self.status}"