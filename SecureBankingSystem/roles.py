from rolepermissions.roles import AbstractUserRole

class ROLE_INDIVIDUAL(AbstractUserRole):
    available_permissions = {

    }

class ROLE_MERCHANT(AbstractUserRole):
    available_permissions = {
        #'edit_patient_file': True,
    }

class ROLE_EMPLOYEE(AbstractUserRole):
    available_permissions = {

    }

class ROLE_MANAGER(AbstractUserRole):
    available_permissions = {

    }

class ROLE_ADMIN(AbstractUserRole):
    available_permissions = {

    }

