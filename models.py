"""
models.py — Pydantic request models for the CIEPAL Submission Report API.
Moved out of backend.py to keep data models in one place.
"""

from pydantic import BaseModel
from typing import Optional


class SubmissionCreate(BaseModel):
    Sub_ID:                             str
    Applicant_ID:                       Optional[str] = None
    Client_Job_ID:                      Optional[str] = None
    Job_Code:                           Optional[str] = None
    Job_Type:                           Optional[str] = None
    Job_Status:                         Optional[str] = None
    Job_Location:                       Optional[str] = None
    States:                             Optional[str] = None
    Number_of_Positions:                Optional[int] = None
    Max_Number_of_Submissions:          Optional[int] = None
    Priority:                           Optional[str] = None
    Client_Category:                    Optional[str] = None
    Email_Address:                      Optional[str] = None
    Applicant_Location:                 Optional[str] = None
    Applicant_Current_Employer:         Optional[str] = None
    Current_Company:                    Optional[str] = None
    Experience:                         Optional[str] = None
    Work_Authorization:                 Optional[str] = None
    Linkedin_URL:                       Optional[str] = None
    Source:                             Optional[str] = None
    Submission_Source:                  Optional[str] = None
    Ownership:                          Optional[str] = None
    Submission_Bill_Rate:               Optional[float] = None
    Submission_Pay_Rate:                Optional[float] = None
    Submission_Tax_Terms:               Optional[str] = None
    Job_Client_Bill_Rate:               Optional[float] = None
    Profile_Status:                     Optional[str] = None
    Pipeline_Status:                    Optional[str] = None
    Applicant_Status:                   Optional[str] = None
    Submission_Rating:                  Optional[str] = None
    Number_of_Interviews:               Optional[int] = None
    Client_Manager:                     Optional[str] = None
    MSP:                                Optional[str] = None
    End_Client:                         Optional[str] = None
    Recruiter_Team_Name:                Optional[str] = None
    Assigned_To_Email_ID:               Optional[str] = None
    Sales_Manager:                      Optional[str] = None
    Submitted_By_Email_ID:              Optional[str] = None
    Status_Changed_By:                  Optional[str] = None
    Applicant_Created_By:               Optional[str] = None
    Account_Manager:                    Optional[str] = None
    Recruitment_Manager:                Optional[str] = None
    Job_Created_By:                     Optional[str] = None
    Job_Applied:                        Optional[str] = None
    Client_Interview_Scheduled_Date:    Optional[str] = None
    Job_Created_On:                     Optional[str] = None
    Applicant_Created_On:               Optional[str] = None
    Submitted_On:                       Optional[str] = None
    Status_Changed_On:                  Optional[str] = None
    Modified_On:                        Optional[str] = None
    Client_Rejection_On:                Optional[str] = None
    RowAdded:                           Optional[str] = None


class SubmissionUpdate(BaseModel):
    Job_Code:                           Optional[str] = None
    Job_Type:                           Optional[str] = None
    Job_Status:                         Optional[str] = None
    Job_Location:                       Optional[str] = None
    States:                             Optional[str] = None
    Number_of_Positions:                Optional[int] = None
    Max_Number_of_Submissions:          Optional[int] = None
    Priority:                           Optional[str] = None
    Client_Category:                    Optional[str] = None
    Email_Address:                      Optional[str] = None
    Applicant_Location:                 Optional[str] = None
    Applicant_Current_Employer:         Optional[str] = None
    Current_Company:                    Optional[str] = None
    Experience:                         Optional[str] = None
    Work_Authorization:                 Optional[str] = None
    Linkedin_URL:                       Optional[str] = None
    Source:                             Optional[str] = None
    Submission_Source:                  Optional[str] = None
    Ownership:                          Optional[str] = None
    Submission_Bill_Rate:               Optional[float] = None
    Submission_Pay_Rate:                Optional[float] = None
    Submission_Tax_Terms:               Optional[str] = None
    Job_Client_Bill_Rate:               Optional[float] = None
    Profile_Status:                     Optional[str] = None
    Pipeline_Status:                    Optional[str] = None
    Applicant_Status:                   Optional[str] = None
    Submission_Rating:                  Optional[str] = None
    Number_of_Interviews:               Optional[int] = None
    Client_Manager:                     Optional[str] = None
    MSP:                                Optional[str] = None
    End_Client:                         Optional[str] = None
    Recruiter_Team_Name:                Optional[str] = None
    Assigned_To_Email_ID:               Optional[str] = None
    Sales_Manager:                      Optional[str] = None
    Submitted_By_Email_ID:              Optional[str] = None
    Status_Changed_By:                  Optional[str] = None
    Applicant_Created_By:               Optional[str] = None
    Account_Manager:                    Optional[str] = None
    Recruitment_Manager:                Optional[str] = None
    Job_Created_By:                     Optional[str] = None
    Client_Interview_Scheduled_Date:    Optional[str] = None
    Client_Rejection_On:                Optional[str] = None
    Applicant_Created_On:               Optional[str] = None
    Submitted_On:                       Optional[str] = None
    Status_Changed_On:                  Optional[str] = None
    Modified_On:                        Optional[str] = None