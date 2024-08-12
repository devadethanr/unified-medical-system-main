function validateName() {
    const nameInput = document.getElementById('name');
    const nameError = document.getElementById('nameError');
    const nameValue = nameInput.value.trim();

    if (nameValue.length < 3 || /[0-9!@#$%^&*()_+}{"':;?/|<>]/.test(nameValue)) {
        nameError.textContent = 'Name must be at least 3 characters and contain no numbers or special characters.';
        return false;
    } else {
        nameError.textContent = '';
        return true;
    }
}

function validateEmail() {
    const emailInput = document.getElementById('email');
    const emailError = document.getElementById('emailError');
    const emailValue = emailInput.value.trim();

    // Basic email format check
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailPattern.test(emailValue)) {
        emailError.textContent = 'Invalid email format.';
        return false;
    } else {
        emailError.textContent = '';
        return true;
    }
}

function validatePhoneNumber() {
    const phoneNumberInput = document.getElementById('phoneNumber');
    const phoneNumberError = document.getElementById('phoneNumberError');
    const phoneNumberValue = phoneNumberInput.value.trim();

    // Phone number format check
    const phonePattern = /^[6-9]\d{9}$/;
    if (!phonePattern.test(phoneNumberValue)) {
        phoneNumberError.textContent = 'Invalid phone number format.';
        return false;
    } else {
        phoneNumberError.textContent = '';
        return true;
    }
}

function validateGender() {
    const genderInput = document.getElementById('gender');
    const genderError = document.getElementById('genderError');
    const genderValue = genderInput.value.trim();

    if (genderValue === '') {
        genderError.textContent = 'Please select a gender.';
        return false;
    } else {
        genderError.textContent = '';
        return true;
    }
}

function validateDateOfBirth() {
    const dateOfBirthInput = document.getElementById('dateOfBirth');
    const dateOfBirthError = document.getElementById('dateOfBirthError');
    const dateOfBirthValue = dateOfBirthInput.value.trim();

    if (dateOfBirthValue === '') {
        dateOfBirthError.textContent = 'Please enter your date of birth.';
        return false;
    } else {
        dateOfBirthError.textContent = '';
        return true;
    }
}

function validateState() {
    const stateInput = document.getElementById('state');
    const stateError = document.getElementById('stateError');
    const stateValue = stateInput.value.trim();

    if (stateValue === '') {
        stateError.textContent = 'Please select a state.';
        return false;
    } else {
        stateError.textContent = '';
        return true;
    }
}

function validateAddress() {
    const addressInput = document.getElementById('address');
    const addressError = document.getElementById('addressError');
    const addressValue = addressInput.value.trim();

    if (addressValue.length < 5) {
        addressError.textContent = 'Address must be at least 5 characters long.';
        return false;
    } else {
        addressError.textContent = '';
        return true;
    }
}

function validateForm() {
    const isNameValid = validateName();
    const isEmailValid = validateEmail();
    const isPhoneNumberValid = validatePhoneNumber();
    const isGenderValid = validateGender();
    const isDateOfBirthValid = validateDateOfBirth();
    const isStateValid = validateState();
    const isAddressValid = validateAddress();

    return isNameValid && isEmailValid && isPhoneNumberValid && isGenderValid && isDateOfBirthValid && isStateValid && isAddressValid;
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('profileForm');

    if (form) {
        form.addEventListener('input', function(event) {
            switch(event.target.id) {
                case 'name':
                    validateName();
                    break;
                case 'email':
                    validateEmail();
                    break;
                case 'phoneNumber':
                    validatePhoneNumber();
                    break;
                case 'gender':
                    validateGender();
                    break;
                case 'dateOfBirth':
                    validateDateOfBirth();
                    break;
                case 'state':
                    validateState();
                    break;
                case 'address':
                    validateAddress();
                    break;
            }
        });

        form.addEventListener('submit', function(event) {
            if (!validateForm()) {
                event.preventDefault(); // Prevent form submission if validation fails
                alert('Please correct the errors in the form before submitting.');
            }
        });
    }
});