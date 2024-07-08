// form-validation.js

function validateName() {
    const nameInput = document.getElementById('name');
    const nameError = document.getElementById('nameError');
    const nameValue = nameInput.value.trim();

    if (nameValue.length < 3) {
        nameError.textContent = 'Name must be at least 3 characters.';
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

function validatePassword() {
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const passwordError = document.getElementById('passwordError');
    const passwordValue = passwordInput.value.trim();
    const confirmPasswordValue = confirmPasswordInput.value.trim();

    // Password strength check
    const passwordPattern = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()_+}{"':;?/|<>]).{8,}$/;
    if (!passwordPattern.test(passwordValue)) {
        passwordError.textContent = 'Password must be at least 8 characters, containing at least one digit, one uppercase letter, one lowercase letter, and one special character.';
        return false;
    } else if (passwordValue !== confirmPasswordValue) {
        passwordError.textContent = 'Passwords do not match.';
        return false;
    } else {
        passwordError.textContent = '';
        return true;
    }
}

// Event listener for keypress on form
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('registerForm');

    form.addEventListener('keyup', function(event) {
        if (event.target.matches('#name')) {
            validateName();
        } else if (event.target.matches('#email')) {
            validateEmail();
        } else if (event.target.matches('#phoneNumber')) {
            validatePhoneNumber();
        } else if (event.target.matches('#password') || event.target.matches('#confirm_password')) {
            validatePassword();
        }
        // Add more conditions for other fields as needed
    });

    // Optional: Final submit validation
    form.addEventListener('submit', function(event) {
        if (!validateName() || !validateEmail() || !validatePhoneNumber() || !validatePassword()) {
            event.preventDefault(); // Prevent form submission if validation fails
            // Optionally, display a general error message if needed
        }
        // Add more validations for other fields before submitting
    });
});
