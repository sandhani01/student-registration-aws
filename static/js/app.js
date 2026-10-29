/**
 * Student Registration System - Frontend Logic
 * AWS Academy Learner Lab Project
 * Handles Client-side Validation, Interactive Feedback, and Form States
 */

document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('registrationForm');
    if (!form) return;

    const submitBtn = document.getElementById('submitBtn');
    const btnSpinner = document.getElementById('btnSpinner');
    const btnIcon = document.getElementById('btnIcon');
    const btnText = document.getElementById('btnText');
    const statusAlert = document.getElementById('statusAlert');

    // Input elements
    const rollNoInput = document.getElementById('roll_no');
    const nameInput = document.getElementById('name');
    const courseInput = document.getElementById('course');
    const yearSelect = document.getElementById('year');
    const emailInput = document.getElementById('email');
    const addressTextarea = document.getElementById('address');

    // Email regex pattern (RFC 5322 compliant structure)
    const emailPattern = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;

    // Clear validation error when user interacts with input
    const inputs = [rollNoInput, nameInput, courseInput, yearSelect, emailInput, addressTextarea];
    inputs.forEach(input => {
        if (!input) return;
        
        input.addEventListener('input', () => {
            clearFieldError(input);
            hideAlert();
        });

        input.addEventListener('change', () => {
            clearFieldError(input);
            hideAlert();
        });
    });

    // Auto-uppercase roll number for consistency
    if (rollNoInput) {
        rollNoInput.addEventListener('blur', () => {
            rollNoInput.value = rollNoInput.value.trim().toUpperCase();
        });
    }

    // Form submission validation
    form.addEventListener('submit', (event) => {
        // Prevent default submission to validate first
        event.preventDefault();

        // Reset previous errors
        let hasErrors = false;
        let firstInvalidInput = null;

        // 1. Validate Roll Number
        const rollNoVal = (rollNoInput.value || '').trim();
        if (!rollNoVal) {
            setFieldError(rollNoInput, 'rollNoError', 'University Roll Number is required.');
            hasErrors = true;
            if (!firstInvalidInput) firstInvalidInput = rollNoInput;
        } else if (rollNoVal.length < 2 || rollNoVal.length > 30) {
            setFieldError(rollNoInput, 'rollNoError', 'Roll Number must be between 2 and 30 characters.');
            hasErrors = true;
            if (!firstInvalidInput) firstInvalidInput = rollNoInput;
        } else {
            clearFieldError(rollNoInput);
            rollNoInput.value = rollNoVal.toUpperCase();
        }

        // 2. Validate Student Name
        const nameVal = (nameInput.value || '').trim();
        if (!nameVal) {
            setFieldError(nameInput, 'nameError', 'Student Name is required.');
            hasErrors = true;
            if (!firstInvalidInput) firstInvalidInput = nameInput;
        } else if (nameVal.length < 2 || nameVal.length > 100) {
            setFieldError(nameInput, 'nameError', 'Name must be between 2 and 100 characters.');
            hasErrors = true;
            if (!firstInvalidInput) firstInvalidInput = nameInput;
        } else {
            clearFieldError(nameInput);
            nameInput.value = nameVal;
        }

        // 3. Validate Course Name
        const courseVal = (courseInput.value || '').trim();
        if (!courseVal) {
            setFieldError(courseInput, 'courseError', 'Course Name is required.');
            hasErrors = true;
            if (!firstInvalidInput) firstInvalidInput = courseInput;
        } else if (courseVal.length < 2 || courseVal.length > 100) {
            setFieldError(courseInput, 'courseError', 'Course Name must be between 2 and 100 characters.');
            hasErrors = true;
            if (!firstInvalidInput) firstInvalidInput = courseInput;
        } else {
            clearFieldError(courseInput);
            courseInput.value = courseVal;
        }

        // 4. Validate Year of Study
        const yearVal = (yearSelect.value || '').trim();
        const validYears = ['Year 1', 'Year 2', 'Year 3', 'Year 4'];
        if (!yearVal || !validYears.includes(yearVal)) {
            setFieldError(yearSelect, 'yearError', 'Please select a valid Year of Study (Years 1 to 4).');
            hasErrors = true;
            if (!firstInvalidInput) firstInvalidInput = yearSelect;
        } else {
            clearFieldError(yearSelect);
        }

        // 5. Validate Email Address
        const emailVal = (emailInput.value || '').trim().toLowerCase();
        if (!emailVal) {
            setFieldError(emailInput, 'emailError', 'Email Address is required.');
            hasErrors = true;
            if (!firstInvalidInput) firstInvalidInput = emailInput;
        } else if (!emailPattern.test(emailVal)) {
            setFieldError(emailInput, 'emailError', 'Please enter a valid email address (e.g. name@university.edu).');
            hasErrors = true;
            if (!firstInvalidInput) firstInvalidInput = emailInput;
        } else {
            clearFieldError(emailInput);
            emailInput.value = emailVal;
        }

        // 6. Validate Address
        const addressVal = (addressTextarea.value || '').trim();
        if (!addressVal) {
            setFieldError(addressTextarea, 'addressError', 'Residential Address is required.');
            hasErrors = true;
            if (!firstInvalidInput) firstInvalidInput = addressTextarea;
        } else if (addressVal.length < 5 || addressVal.length > 500) {
            setFieldError(addressTextarea, 'addressError', 'Address must be between 5 and 500 characters.');
            hasErrors = true;
            if (!firstInvalidInput) firstInvalidInput = addressTextarea;
        } else {
            clearFieldError(addressTextarea);
            addressTextarea.value = addressVal;
        }

        // If validation errors exist, focus first field and show alert
        if (hasErrors) {
            if (firstInvalidInput) {
                firstInvalidInput.focus();
            }
            showAlert('danger', 'Validation Notice', 'Please correct the highlighted fields before submitting.');
            return;
        }

        // If client-side validation passed, activate loading state
        setLoadingState(true);

        // Submit form natively to render success or error Jinja template
        form.submit();
    });

    /**
     * Set visual error state on a specific input field
     */
    function setFieldError(inputElement, errorElementId, message) {
        if (!inputElement) return;
        inputElement.classList.add('is-invalid');
        const errEl = document.getElementById(errorElementId);
        if (errEl) {
            errEl.textContent = message;
        }
    }

    /**
     * Clear visual error state from an input field
     */
    function clearFieldError(inputElement) {
        if (!inputElement) return;
        inputElement.classList.remove('is-invalid');
        const errEl = document.getElementById(inputElement.id + 'Error');
        if (errEl) {
            errEl.textContent = '';
        }
    }

    /**
     * Toggle the submit button loading state
     */
    function setLoadingState(isLoading) {
        if (!submitBtn) return;
        submitBtn.disabled = isLoading;

        if (isLoading) {
            if (btnSpinner) btnSpinner.classList.remove('d-none');
            if (btnIcon) btnIcon.classList.add('d-none');
            if (btnText) btnText.textContent = 'Saving to DynamoDB & SNS...';
        } else {
            if (btnSpinner) btnSpinner.classList.add('d-none');
            if (btnIcon) btnIcon.classList.remove('d-none');
            if (btnText) btnText.textContent = 'Register Student';
        }
    }

    /**
     * Display contextual alert box
     */
    function showAlert(type, heading, message) {
        if (!statusAlert) return;
        statusAlert.className = `alert-box alert-${type}-box`;
        const headingEl = document.getElementById('alertHeading');
        const messageEl = document.getElementById('alertMessage');
        if (headingEl) headingEl.textContent = heading;
        if (messageEl) messageEl.textContent = message;
        statusAlert.classList.remove('d-none');
    }

    /**
     * Hide alert box
     */
    function hideAlert() {
        if (statusAlert) {
            statusAlert.classList.add('d-none');
        }
    }

    // Expose dismiss function globally for close button
    window.dismissAlert = hideAlert;

    // Expose reset function
    window.resetForm = function() {
        form.reset();
        inputs.forEach(input => clearFieldError(input));
        hideAlert();
        setLoadingState(false);
    };
});
