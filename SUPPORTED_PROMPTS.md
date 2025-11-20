# Supported Prompts

This document lists all supported prompts for the SD Elements MCP Server, organized by area.

## Applications

### create_application

- Create a new application called Customer Portal
- Create application Customer Portal in business unit 2
- I need to register a new application called Customer Portal
- Register Customer Portal as a new application
- Set up a new application entry for Customer Portal

### get_application

- Get application 123
- Get application details for ID 123
- I need information about application 123 for planning
- Show me details for application 123
- What's the security status of application 123?

### list_applications

- List all applications
- Show me all applications
- Show me all the apps in our security program
- What applications are we tracking?
- What applications do we have?

### update_application

- Modify application 123 description
- Modify application 123 details
- Update application 123 description
- Update the description for application 123

---

## Business Units

### get_business_unit

- Get business unit 123
- Get business unit information for ID 123
- Show me details for business unit 123
- What's business unit 123?

### list_business_units

- List all business units
- Show me all business units
- Show me all the departments we track
- What business units are in the system?
- What business units do we have?

---

## Connection

### test_connection

- Can you verify our SD Elements integration is up?
- Check if the security API is accessible
- Is the API connection working?
- Test if the API connection works
- Test the connection to SD Elements
- Validate the API connection
- Verify the API connection is working
- Verify the connection

---

## Countermeasures

### add_countermeasure_note

- Add a note about countermeasure 123
- Add a note to countermeasure 123
- Add compliance notes to countermeasure 123
- Add security notes to countermeasure 123
- Document countermeasure 123 with a note
- Document that we've implemented countermeasure 123

### get_countermeasure

- Get countermeasure 789
- Get countermeasure details for 789
- I need details on countermeasure 789 for my audit
- Show me details for countermeasure 789
- What's the status of countermeasure 789?

### list_countermeasures

- List all countermeasures for project 123
- List all security countermeasures for project 123
- Show me all countermeasures for project 123
- Show me countermeasures for project 456
- Show me what security tasks are pending for project 456
- What security controls are implemented for project 123?
- What security controls are in place for project 123?

### update_countermeasure

- Mark countermeasure 123 as completed
- Mark countermeasure 123 as implemented
- Set countermeasure 123 status to completed
- Update countermeasure 123 status to completed
- Update countermeasure 123 to completed
- Update countermeasure 123 to reflect our compliance status

---

## Diagrams

### create_diagram

- Add a threat model diagram for project 123
- Create a new diagram for project 123
- Create a new diagram to document project 123
- I need to create a diagram for project 123

### delete_diagram

- Delete diagram 789
- Delete the obsolete diagram 789
- Remove diagram 789
- Remove diagram 789 as it's outdated

### get_diagram

- Get diagram 456
- Get diagram details for ID 456
- Get the details for diagram 456
- Show me diagram 456

### list_project_diagrams

- List all diagrams for project 123
- Show me all diagrams for project 123
- Show me the threat model diagrams for project 123
- What diagrams exist for project 123?

### update_diagram

- Modify diagram 456
- Modify diagram 456 with new information
- Update diagram 456
- Update the diagram 456 details
- Update the diagram for project 456

---

## Generic

### api_request

- Call the API endpoint for projects
- Execute a custom API request
- Make a GET request to projects/123/
- Make a custom API call to projects/123/

---

## Projects

### create_project

- Create a new mobile project for our iOS app
- Create a new project called My Project
- Create a new project called My Project in application 5
- Create an API project for our microservices
- I need to set up a new project called My Project
- I need to set up a new project for the Q4 initiative
- Let's create a project for the new microservice we're building
- Set up a new security project called My Project
- Set up a web application project

### create_project_from_code

- Create a project by scanning a code repository
- Create a project from code repository
- Initialize a project from the repository scan
- Scan repository and create project
- Set up a project by scanning the code repository

### delete_project

- Archive project 456 as it's been completed
- Delete project 456
- Remove project 456 from the system
- Remove the deprecated project 456

### get_project

- Get details for project 123
- Get project details for ID 123
- I need details on project 123 for my status report
- Show me information about project ID 456
- Show me the security posture for project 456
- What is project 789?
- What's the security posture of project 123?
- What's the status of project 123?

### list_profiles

- List all profiles
- Show me all available profiles
- Show me the available project profiles
- What profiles are available?
- What security profiles are available?

### list_risk_policies

- List all risk policies
- Show me all available risk policies
- What risk policies are available?
- Get me a list of risk policies

### get_risk_policy

- Get risk policy 5
- Show me details for risk policy 3
- What is risk policy 2?

### list_projects

- Can you show me all active projects?
- Get me a list of all projects
- List all projects
- List all projects in the system
- Show me all projects for security review
- Show me all the projects in SD Elements
- What projects are available?
- What projects are we currently tracking?
- What projects do we have in the system?

### update_project

- Change project 123 name to New Name
- Rename project 123 to match our new branding
- Update project 123 name to New Name
- Update project 123 with new name
- Update the project status to reflect current sprint progress
- Set the risk policy for project 123 to 5
- Update project 456 risk policy to 3

---

## Reports

### create_advanced_report

- Create a new report called Security Status
- Create a report called Security Status
- Create a report to track project progress
- I need a custom report for security metrics
- I need a new report called Security Status

### execute_cube_query

- Execute a Cube query for security trends
- Query security metrics using Cube
- Query the data cube for project metrics
- Run a Cube query to analyze security trends
- Run a custom query to analyze security trends

### get_advanced_report

- Get details for report 456
- Get report configuration for ID 456
- Show me details for report 456
- Show me the configuration for report 456
- What does report 456 show?

### list_advanced_reports

- List all reports
- Show me all available reports
- Show me all the security reports available
- What reports are available?
- What reports can I generate?
- What security reports can I run?

### run_advanced_report

- Generate report 123
- Generate report 123 for my status update
- Run report 123
- Run the security compliance report

---

## Scans

### get_scan_status

- Get scan status for scan 456
- Get status for scan 456
- Is scan 456 complete?
- Is scan 456 finished?
- What's the status of scan 456?

### list_scan_connections

- List scan connections
- Show me all scan connections
- Show me available repository scan connections
- What repository connections are available?
- What repository connections are configured?

### list_scans

- List all scans for project 123
- Show me all repository scans for project 123
- Show me all scans for project 123
- What scans have been run for project 123?

### scan_repository

- Run a code scan on the repo for project 123
- Scan repository https://github.com/org/repo for project 123
- Scan the repository for project 123
- Scan the repository to auto-populate the project survey

---

## Surveys

### add_survey_answers_by_text

- Add Python as a technology for project 123
- Add Python to project 123 survey
- Add Python to the survey for project 123
- Update project 123 to include Python in the survey
- We're adding Python to the tech stack for project 123

### commit_survey_draft

- Commit the survey draft for project 123
- Finalize and commit the survey draft
- Publish the survey for project 123

### find_survey_answers

- Find answer IDs for Python and Django
- Find survey answers for Python and Django
- Look up the survey answer IDs for Python and Django
- Search for Python and Django in the survey answers
- Search for survey answers matching Python and Django

### get_project_survey

- Get the survey for project 123
- Get the survey structure for project 123
- I need to see what survey questions are available for project 123
- Show me the survey template for project 123
- What survey questions are available for project 123?

### get_survey_answers_for_project

- Get the survey answers for project 456
- Show me the survey answers for project 456
- Show me what's currently set in the survey for project 456
- What answers are configured for project 456?
- What technologies are configured for project 456?

### remove_survey_answers_by_text

- Remove Java from project 456
- Remove Java from project 456 survey
- Remove Java from the project survey as we've migrated away
- Remove Java from the survey for project 456
- We're deprecating Java in project 456

### set_project_survey_by_text

- Configure project 123 with Python Django PostgreSQL
- Configure project 123 with Python, Django, and PostgreSQL
- Set survey for project 123 to Python Django PostgreSQL
- Set the complete technology stack for project 123
- Set the survey for project 123 to Python Django PostgreSQL

### update_project_survey

- Modify survey answers for project 123
- Update survey answers for project 123
- Update survey answers using IDs for project 123
- Update the survey configuration for project 123
- Update the survey using answer IDs for project 123

---

## Users

### get_current_user

- Get my current user information
- Show me my user profile
- What's my user account?
- Who am I?

### get_user

- Get user 123
- Get user information for ID 123
- Show me details for user 123
- Show me information about user 123
- Who is user 123?

### list_users

- List all users
- Show me all active users
- Show me all users
- Show me the team members in the system
- Who are the users in the system?
- Who has access to SD Elements?

---
