-- ============================================================
--   STUDENT DATABASE MANAGEMENT SYSTEM
--   STEP 1: Run this file FIRST in SQL Command Line
--   Command: @C:\student_project\STEP1_database_setup.sql
-- ============================================================

-- Connect first (run this manually):
-- CONNECT system/your_password@XE

SET SERVEROUTPUT ON;
SET LINESIZE 200;
SET PAGESIZE 100;


-- ============================================================
-- SECTION 1: DROP OLD TABLES (if rerunning this script)
-- ============================================================
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE Enrollment CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN NULL;
END;
/
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE Course CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN NULL;
END;
/
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE Student CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN NULL;
END;
/
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE Faculty CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN NULL;
END;
/
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE Department CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN NULL;
END;
/
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE Audit_Log CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN NULL;
END;
/
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE Admin_Users CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN NULL;
END;
/

-- Drop sequences if they exist
BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE audit_seq'; EXCEPTION WHEN OTHERS THEN NULL; END;
/
BEGIN EXECUTE IMMEDIATE 'DROP SEQUENCE enrollment_seq'; EXCEPTION WHEN OTHERS THEN NULL; END;
/


-- ============================================================
-- SECTION 2: DDL - CREATE TABLES
-- ============================================================

-- TABLE 1: Department
CREATE TABLE Department (
    Department_ID   NUMBER(5)    PRIMARY KEY,
    Department_Name VARCHAR2(100) NOT NULL,
    Email           VARCHAR2(100),
    Location        VARCHAR2(100)
);

-- TABLE 2: Faculty
CREATE TABLE Faculty (
    Faculty_ID    NUMBER(5)    PRIMARY KEY,
    First_Name    VARCHAR2(50) NOT NULL,
    Last_Name     VARCHAR2(50) NOT NULL,
    Email         VARCHAR2(100) UNIQUE,
    Phone         VARCHAR2(20),
    Department_ID NUMBER(5),
    CONSTRAINT fk_faculty_dept FOREIGN KEY (Department_ID)
        REFERENCES Department(Department_ID)
);

-- TABLE 3: Student
CREATE TABLE Student (
    Student_ID  NUMBER(7)    PRIMARY KEY,
    First_Name  VARCHAR2(50) NOT NULL,
    Last_Name   VARCHAR2(50) NOT NULL,
    Email       VARCHAR2(100) UNIQUE,
    Phone       VARCHAR2(20),
    Faculty_ID  NUMBER(5),
    CONSTRAINT fk_student_faculty FOREIGN KEY (Faculty_ID)
        REFERENCES Faculty(Faculty_ID)
);

-- TABLE 4: Course
CREATE TABLE Course (
    Course_Code   VARCHAR2(10)  PRIMARY KEY,
    Course_Name   VARCHAR2(100) NOT NULL,
    Credits       NUMBER(2),
    Semester      VARCHAR2(20),
    Department_ID NUMBER(5),
    CONSTRAINT fk_course_dept FOREIGN KEY (Department_ID)
        REFERENCES Department(Department_ID)
);

-- TABLE 5: Enrollment (Junction table - Student M:M Course)
CREATE TABLE Enrollment (
    Enrollment_ID NUMBER(10)   PRIMARY KEY,
    Student_ID    NUMBER(7),
    Course_Code   VARCHAR2(10),
    Enroll_Date   DATE DEFAULT SYSDATE,
    Grade         VARCHAR2(2),
    CONSTRAINT fk_enroll_student FOREIGN KEY (Student_ID)
        REFERENCES Student(Student_ID),
    CONSTRAINT fk_enroll_course FOREIGN KEY (Course_Code)
        REFERENCES Course(Course_Code)
);

-- TABLE 6: Audit Log (used by triggers)
CREATE TABLE Audit_Log (
    Log_ID      NUMBER(10)   PRIMARY KEY,
    Action_Type VARCHAR2(20),
    Table_Name  VARCHAR2(50),
    Action_Date DATE DEFAULT SYSDATE,
    Done_By     VARCHAR2(50)
);

-- TABLE 7: Admin Users (for login)
CREATE TABLE Admin_Users (
    User_ID   NUMBER(5)    PRIMARY KEY,
    Username  VARCHAR2(50) UNIQUE NOT NULL,
    Password  VARCHAR2(50) NOT NULL,
    Role      VARCHAR2(20) DEFAULT 'user'
);

-- Sequences
CREATE SEQUENCE audit_seq      START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE enrollment_seq START WITH 1 INCREMENT BY 1;

-- ============================================================
-- SECTION 3: DDL - ALTER TABLE (demonstrating ALTER)
-- ============================================================

ALTER TABLE Student ADD Date_of_Birth DATE;
ALTER TABLE Student MODIFY Phone VARCHAR2(20);
ALTER TABLE Student DROP COLUMN Date_of_Birth;

-- ============================================================
-- SECTION 4: DML - INSERT SAMPLE DATA
-- ============================================================

-- Departments
INSERT INTO Department VALUES (1, 'Computer Science', 'cs@uni.edu', 'Block 2');
INSERT INTO Department VALUES (2, 'Mathematics',      'math@uni.edu', 'Block 3');
INSERT INTO Department VALUES (3, 'Physics',          'phy@uni.edu', 'Block 1');
INSERT INTO Department VALUES (4, 'Electronics',      'ec@uni.edu', 'Block 4');
INSERT INTO Department VALUES (5, 'Management',       'mgmt@uni.edu', 'Block 5');

-- Faculty
INSERT INTO Faculty VALUES (101, 'Bindu',  'Madhavi',    'bindu@uni.edu',    '9001001001', 1);
INSERT INTO Faculty VALUES (102, 'Anirban', 'Roy',   'anirban@uni.edu',   '9001001002', 2);
INSERT INTO Faculty VALUES (103, 'Janita',  'Saji',   'janita@uni.edu',   '9001001003', 1);
INSERT INTO Faculty VALUES (104, 'Baburaj', 'M',    'baburaj@uni.edu',    '9001001004', 3);
INSERT INTO Faculty VALUES (105, 'Deepaa',   'Suresh', 'deepaa@uni.edu', '9001001005', 4);

-- Students
INSERT INTO Student VALUES (2001, 'Swara',  'Madichedi',  'swara@student.edu',  '9900001001', 101);
INSERT INTO Student VALUES (2002, 'Lalit',  'Kumar', 'lalit@student.edu',  '9900001002', 101);
INSERT INTO Student VALUES (2003, 'Charushree',  'S',  'charushree@student.edu',  '9900001003', 102);
INSERT INTO Student VALUES (2004, 'Sricharan',  'A',  'sricharan@student.edu',  '9900001004', 103);
INSERT INTO Student VALUES (2005, 'Kiran',  'Rao',    'kiran@student.edu',  '9900001005', 104);
INSERT INTO Student VALUES (2006, 'Vikram', 'Singh',  'vikram@student.edu', '9900001006', 102);
INSERT INTO Student VALUES (2007, 'Meera',  'Nair',   'meera@student.edu',  '9900001007', 105);

-- Courses
INSERT INTO Course VALUES ('CS101', 'Intro to Programming', 4, 'Semester 1', 1);
INSERT INTO Course VALUES ('CS201', 'Data Structures',      4, 'Semester 2', 1);
INSERT INTO Course VALUES ('MA101', 'Calculus',             3, 'Semester 1', 2);
INSERT INTO Course VALUES ('PH101', 'Physics Basics',       3, 'Semester 1', 3);
INSERT INTO Course VALUES ('EC101', 'Circuit Theory',       4, 'Semester 2', 4);

-- Enrollments
INSERT INTO Enrollment VALUES (enrollment_seq.NEXTVAL, 2001, 'CS101', SYSDATE, 'A');
INSERT INTO Enrollment VALUES (enrollment_seq.NEXTVAL, 2001, 'MA101', SYSDATE, 'B');
INSERT INTO Enrollment VALUES (enrollment_seq.NEXTVAL, 2002, 'CS101', SYSDATE, 'A');
INSERT INTO Enrollment VALUES (enrollment_seq.NEXTVAL, 2002, 'CS201', SYSDATE, 'B');
INSERT INTO Enrollment VALUES (enrollment_seq.NEXTVAL, 2003, 'MA101', SYSDATE, 'C');
INSERT INTO Enrollment VALUES (enrollment_seq.NEXTVAL, 2004, 'CS201', SYSDATE, 'B');
INSERT INTO Enrollment VALUES (enrollment_seq.NEXTVAL, 2005, 'PH101', SYSDATE, 'A');
INSERT INTO Enrollment VALUES (enrollment_seq.NEXTVAL, 2006, 'EC101', SYSDATE, 'B');
INSERT INTO Enrollment VALUES (enrollment_seq.NEXTVAL, 2007, 'CS101', SYSDATE, 'A');

-- Admin Users (for login system)
INSERT INTO Admin_Users VALUES (1, 'admin', 'admin123', 'admin');
INSERT INTO Admin_Users VALUES (2, 'user',  'user123',  'user');

COMMIT;

-- ============================================================
-- SECTION 5: DML - UPDATE and DELETE examples
-- ============================================================

UPDATE Student SET Phone = '9999999999' WHERE Student_ID = 2001;
DELETE FROM Enrollment WHERE Student_ID = 2005 AND Course_Code = 'PH101';
COMMIT;


-- ============================================================
-- SECTION 6: TCL - SAVEPOINT and ROLLBACK demo
-- ============================================================

SAVEPOINT before_test_update;
UPDATE Student SET Phone = '0000000000' WHERE Student_ID = 2002;
ROLLBACK TO before_test_update;
COMMIT;


-- ============================================================
-- SECTION 7: ALL SQL CLAUSES DEMO
-- ============================================================

-- WHERE
SELECT * FROM Student WHERE Faculty_ID = 101;

-- ORDER BY
SELECT * FROM Student ORDER BY Last_Name ASC;

-- DISTINCT
SELECT DISTINCT Faculty_ID FROM Student;

-- GROUP BY + HAVING
SELECT Course_Code, COUNT(*) AS Total_Students
FROM Enrollment
GROUP BY Course_Code
HAVING COUNT(*) > 1;

-- LIKE
SELECT * FROM Student WHERE Email LIKE '%@student.edu';

-- IN
SELECT * FROM Course WHERE Department_ID IN (1, 2, 3);

-- BETWEEN
SELECT * FROM Enrollment
WHERE Enroll_Date BETWEEN DATE '2020-01-01' AND SYSDATE;


-- ============================================================
-- SECTION 8: ALL JOINS
-- ============================================================

-- INNER JOIN
SELECT s.Student_ID, s.First_Name, f.First_Name AS Faculty_Name
FROM Student s
INNER JOIN Faculty f ON s.Faculty_ID = f.Faculty_ID;

-- LEFT JOIN
SELECT s.First_Name, e.Course_Code
FROM Student s
LEFT JOIN Enrollment e ON s.Student_ID = e.Student_ID;

-- RIGHT JOIN
SELECT s.First_Name, e.Course_Code
FROM Student s
RIGHT JOIN Enrollment e ON s.Student_ID = e.Student_ID;

-- FULL OUTER JOIN
SELECT s.First_Name, e.Course_Code
FROM Student s
FULL OUTER JOIN Enrollment e ON s.Student_ID = e.Student_ID;

-- SELF JOIN (students under same faculty)
SELECT a.First_Name AS Student1, b.First_Name AS Student2, a.Faculty_ID
FROM Student a, Student b
WHERE a.Faculty_ID = b.Faculty_ID
  AND a.Student_ID != b.Student_ID;


-- ============================================================
-- SECTION 9: AGGREGATE FUNCTIONS
-- ============================================================

SELECT COUNT(*) AS Total_Students FROM Student;
SELECT AVG(Credits)  AS Avg_Credits  FROM Course;
SELECT MAX(Credits)  AS Max_Credits  FROM Course;
SELECT MIN(Credits)  AS Min_Credits  FROM Course;
SELECT SUM(Credits)  AS Total_Credits FROM Course;


-- ============================================================
-- SECTION 10: STRING FUNCTIONS
-- ============================================================

SELECT
    UPPER(First_Name)                        AS Upper_Name,
    LOWER(Last_Name)                         AS Lower_Name,
    LENGTH(Email)                            AS Email_Length,
    CONCAT(First_Name, ' ') || Last_Name    AS Full_Name,
    SUBSTR(Email, 1, 5)                      AS Email_Preview,
    TRIM(Phone)                              AS Clean_Phone
FROM Student;


-- ============================================================
-- SECTION 11: DATE FUNCTIONS
-- ============================================================

SELECT
    SYSDATE                              AS Today,
    ADD_MONTHS(SYSDATE, 6)              AS Six_Months_Later,
    EXTRACT(YEAR  FROM Enroll_Date)     AS Enroll_Year,
    EXTRACT(MONTH FROM Enroll_Date)     AS Enroll_Month,
    SYSDATE - Enroll_Date               AS Days_Since_Enrollment
FROM Enrollment;


-- ============================================================
-- SECTION 12: VIEWS
-- ============================================================

CREATE OR REPLACE VIEW vw_Student_Details AS
SELECT
    s.Student_ID,
    s.First_Name || ' ' || s.Last_Name AS Full_Name,
    s.Email,
    s.Phone,
    f.First_Name || ' ' || f.Last_Name AS Faculty_Name,
    d.Department_Name
FROM Student s
JOIN Faculty    f ON s.Faculty_ID    = f.Faculty_ID
JOIN Department d ON f.Department_ID = d.Department_ID;

CREATE OR REPLACE VIEW vw_Course_Enrollment AS
SELECT
    c.Course_Code,
    c.Course_Name,
    c.Credits,
    COUNT(e.Student_ID) AS Enrolled_Count
FROM Course c
LEFT JOIN Enrollment e ON c.Course_Code = e.Course_Code
GROUP BY c.Course_Code, c.Course_Name, c.Credits;

CREATE OR REPLACE VIEW vw_Department_Report AS
SELECT
    d.Department_Name,
    COUNT(DISTINCT f.Faculty_ID)  AS Faculty_Count,
    COUNT(DISTINCT s.Student_ID)  AS Student_Count
FROM Department d
LEFT JOIN Faculty  f ON d.Department_ID = f.Department_ID
LEFT JOIN Student  s ON f.Faculty_ID    = s.Faculty_ID
GROUP BY d.Department_Name;

-- Use the views
SELECT * FROM vw_Student_Details;
SELECT * FROM vw_Course_Enrollment;
SELECT * FROM vw_Department_Report;


-- ============================================================
-- SECTION 13: TRIGGERS
-- ============================================================

-- TRIGGER 1: BEFORE INSERT on Student - validate email
CREATE OR REPLACE TRIGGER trg_before_student_insert
BEFORE INSERT ON Student
FOR EACH ROW
BEGIN
    IF :NEW.Email NOT LIKE '%@%' THEN
        RAISE_APPLICATION_ERROR(-20001, 'Invalid email! Must contain @');
    END IF;
END;
/

-- TRIGGER 2: AFTER INSERT on Enrollment - write audit log
CREATE OR REPLACE TRIGGER trg_after_enrollment_insert
AFTER INSERT ON Enrollment
FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log VALUES (
        audit_seq.NEXTVAL,
        'INSERT',
        'Enrollment',
        SYSDATE,
        USER
    );
END;
/

-- TRIGGER 3: AFTER DELETE on Student - write audit log
CREATE OR REPLACE TRIGGER trg_after_student_delete
AFTER DELETE ON Student
FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log VALUES (
        audit_seq.NEXTVAL,
        'DELETE',
        'Student',
        SYSDATE,
        USER
    );
END;
/

-- TRIGGER 4: BEFORE UPDATE on Student - log updates
CREATE OR REPLACE TRIGGER trg_before_student_update
BEFORE UPDATE ON Student
FOR EACH ROW
BEGIN
    INSERT INTO Audit_Log VALUES (
        audit_seq.NEXTVAL,
        'UPDATE',
        'Student',
        SYSDATE,
        USER
    );
END;
/


-- ============================================================
-- SECTION 14: CURSOR
-- ============================================================

DECLARE
    CURSOR cur_student_courses IS
        SELECT
            s.First_Name || ' ' || s.Last_Name AS Student_Name,
            c.Course_Name,
            e.Grade,
            d.Department_Name
        FROM Student s
        JOIN Enrollment e  ON s.Student_ID   = e.Student_ID
        JOIN Course     c  ON e.Course_Code  = c.Course_Code
        JOIN Faculty    f  ON s.Faculty_ID   = f.Faculty_ID
        JOIN Department d  ON f.Department_ID = d.Department_ID
        ORDER BY s.Student_ID;

    v_name   VARCHAR2(100);
    v_course VARCHAR2(100);
    v_grade  VARCHAR2(2);
    v_dept   VARCHAR2(100);
BEGIN
    DBMS_OUTPUT.PUT_LINE('====== STUDENT ENROLLMENT REPORT ======');
    DBMS_OUTPUT.PUT_LINE('---------------------------------------');

    OPEN cur_student_courses;
    LOOP
        FETCH cur_student_courses INTO v_name, v_course, v_grade, v_dept;
        EXIT WHEN cur_student_courses%NOTFOUND;

        DBMS_OUTPUT.PUT_LINE(
            'Student : ' || v_name      || CHR(10) ||
            'Course  : ' || v_course    || CHR(10) ||
            'Grade   : ' || v_grade     || CHR(10) ||
            'Dept    : ' || v_dept      || CHR(10) ||
            '---------------------------------------'
        );
    END LOOP;

    DBMS_OUTPUT.PUT_LINE('Total rows processed: ' || cur_student_courses%ROWCOUNT);
    CLOSE cur_student_courses;
END;
/


-- ============================================================
-- SECTION 15: DCL - GRANT and REVOKE
-- ============================================================

-- NOTE: Run these as SYSTEM user
-- CREATE USER student_user IDENTIFIED BY pass123;
-- GRANT CONNECT TO student_user;
-- GRANT SELECT, INSERT, UPDATE ON Student    TO student_user;
-- GRANT SELECT, INSERT, UPDATE ON Faculty    TO student_user;
-- GRANT SELECT, INSERT, UPDATE ON Course     TO student_user;
-- GRANT SELECT, INSERT, UPDATE ON Department TO student_user;
-- GRANT SELECT ON Enrollment TO student_user;
-- REVOKE INSERT ON Student FROM student_user;


-- ============================================================
-- SECTION 16: TRUNCATE demo (on audit log - safe to clear)
-- ============================================================

-- TRUNCATE TABLE Audit_Log;
-- (Commented out so audit logs are preserved - uncomment if needed)


-- ============================================================
-- DONE! All tables, data, views, triggers and cursor are ready.
-- Now run: python app.py
-- Then open browser: http://127.0.0.1:5000
-- ============================================================

SELECT 'DATABASE SETUP COMPLETE!' AS Status FROM DUAL;
