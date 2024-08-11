// form-validation.js

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

function validatePassword() {
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const passwordError = document.getElementById('passwordError');
    const passwordValue = passwordInput.value.trim();
    const confirmPasswordValue = confirmPasswordInput.value.trim();

    // Password strength check
    const passwordPattern = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[!@#$%^&*()_+}{"':;?/|<>]).{8,}$/;
    if (!passwordPattern.test(passwordValue)) {
        passwordError.textContent = 'Please use a stronger password.';
        return false;
    } else if (passwordValue !== confirmPasswordValue) {
        passwordError.textContent = 'Passwords do not match.';
        return false;
    } else {
        passwordError.textContent = '';
        return true;
    }
}

function validateSpecialization() {
  const specializationInput = document.getElementById('specialization');
  const specializationError = document.getElementById('specializationError');
  const specializationValue = specializationInput.value.trim();

  if (specializationValue.length < 3) {
    specializationError.textContent = 'Specialization must be at least 3 characters.';
    return false;
  } else {
    specializationError.textContent = '';
    return true;
  }
}

function validateMedicalId() {
   const medicalIdInput = document.getElementById('medicalId');
   const medicalIdError = document.getElementById('medicalIdError');
   const medicalIdValue = medicalIdInput.value.trim();

   const licensePattern = /^[A-Z]{2}-\d{2}-\d{4}-\d{7}$/;
   if (!licensePattern.test(medicalIdValue)) {
      medicalIdError.textContent = 'Invalid medical ID format. Please use XX-YY-ZZZZ-NNNNNNN';
      return false;
   } else {
      medicalIdError.textContent = '';
      return true;
   }
}

function validateQualification() {
  const qualificationInput = document.getElementById('qualification');
  const qualificationError = document.getElementById('qualificationError');
  const qualificationValue = qualificationInput.value.trim();

  if (qualificationValue.length < 3) {
    qualificationError.textContent = 'Qualification must be at least 3 characters.';
    return false;
  } else {
    qualificationError.textContent = '';
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

// Event listener for keypress on form
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
            case 'specialization':
               validateSpecialization();
               break;
            case 'medicalId':
               validateMedicalId();
               break;
            case 'qualification':
               validateQualification();
               break;
            case 'address':
               validateAddress();
               break;
         }
      });

      // Final submit validation
      form.addEventListener('submit', function(event) {
         if (!validateName() || !validateEmail() || !validatePhoneNumber() || 
             !validateSpecialization() || !validateMedicalId() || !validateQualification() || 
             !validateAddress()) {
            event.preventDefault(); // Prevent form submission if validation fails
            alert('Please correct the errors in the form before submitting.');
         }
      });
   }
});