"use strict";

/* ==========================================
   K Wallet v2
========================================== */

/* ==========================================
   Helpers
========================================== */

const $ = (id) => document.getElementById(id);

const API = {
    register: "/register",
    login: "/login",
    logout: "/logout",
    balance: "/balance",
    send: "/send",
    history: "/history",
    uploadPhoto: "/upload_photo"
};

/* ==========================================
   Request Helper
========================================== */

async function request(url, options = {}) {

    try {

        const response = await fetch(url, options);
        return await response.json();

    } catch (error) {

        console.error(error);
        showNotification("Network Error", "danger");
        return null;

    }

}

/* ==========================================
   Notifications
========================================== */

function showNotification(message, type = "success") {

    const box = $("notification");

    if (!box) {
        alert(message);
        return;
    }

    box.innerHTML = message;
    box.className = type;
    box.style.display = "block";

    setTimeout(() => {
        box.style.display = "none";
    }, 3000);

}

/* ==========================================
   Navigation
========================================== */

function openLogin() {
    window.location = "/login-page";
}

function openRegister() {
    window.location = "/register-page";
}

/* ==========================================
   Register
========================================== */

async function registerUser() {

    const username = $("registerUsername").value.trim();
    const pin = $("registerPin").value.trim();

    if (username === "" || pin === "") {
        showNotification("Please fill in all fields.", "warning");
        return;
    }

    const data = await request(API.register, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username: username,
            pin: pin
        })
    });

    if (!data) return;

    if (data.error) {
        showNotification(data.error, "danger");
        return;
    }

    alert(
        "Account Created!\n\n" +
        "Account Number: " + data.account
    );

    window.location = "/login-page";

}

/* ==========================================
   Login
========================================== */

async function loginUser() {

    const account = $("loginAccount").value.trim();
    const pin = $("loginPin").value.trim();

    if (account === "" || pin === "") {
        showNotification("Please fill in all fields.", "warning");
        return;
    }

    const data = await request(API.login, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            account: account,
            pin: pin
        })
    });

    if (!data) return;

    if (data.error) {
        showNotification(data.error, "danger");
        return;
    }

    showNotification("Login successful!");

    setTimeout(() => {
        window.location = "/dashboard";
    }, 1000);

}

/* ==========================================
   Logout
========================================== */

function logoutUser() {
    window.location = API.logout;
}