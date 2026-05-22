document.addEventListener(
    "DOMContentLoaded",
    () => {

        initPassword();

        initLogin();

        checkAuth();

    }
);


function initPassword(){

    const toggle =
        document.getElementById(
            "togglePassword"
        );

    const password =
        document.getElementById(
            "password"
        );

    if(
        !toggle ||
        !password
    ){
        return;
    }

    toggle.addEventListener(
        "click",
        e=>{

            e.preventDefault();

            const type =
                password.type ===
                "password"
                ? "text"
                : "password";

            password.type =
                type;

            toggle.textContent =
                type === "password"
                ? "👁️"
                : "👁️‍🗨️";

        }
    );

}


function initLogin(){

    const form =
        document.getElementById(
            "loginForm"
        );

    if(
        !form
    ){
        return;
    }

    form.onsubmit =
    async e=>{

        e.preventDefault();

        await performLogin(
            document.getElementById(
                "username"
            ).value,

            document.getElementById(
                "password"
            ).value
        );

    };

}


function showToast(
    message,
    type="error"
){

    const container =
        document.getElementById(
            "toast-container"
        );

    const toast =
        document.createElement(
            "div"
        );

    toast.className =
        `toast-msg ${type}`;

    toast.textContent =
        message;

    container.appendChild(
        toast
    );

    setTimeout(
        ()=>toast.remove(),
        3000
    );

}


async function performLogin(
    username,
    password
){

    const formData =
        new FormData();

    formData.append(
        "username",
        username
    );

    formData.append(
        "password",
        password
    );

    try{

        const response =
        await fetch(
            "/api/auth/login",
            {
                method:"POST",
                body:formData
            }
        );

        const result =
        await response.json();

        if(
            result.success
        ){

            showToast(
                "Login berhasil",
                "success"
            );

            setTimeout(
                ()=>{
                    window.location.reload();
                },
                1000
            );

        }else{

            showToast(
                result.message
            );

        }

    }catch{

        showToast(
            "Koneksi gagal"
        );

    }

}


async function performLogout(){

    await fetch(
        "/api/auth/logout",
        {
            method:"POST"
        }
    );

    window.location.reload();

}


async function checkAuth(){

    try{

        const res =
        await fetch(
            "/api/orders/masuk"
        );

        if(
            res.status===401
        ){

            document
            .getElementById(
                "loginPage"
            )
            .style.display=
            "flex";

            return;

        }

        document
        .getElementById(
            "mainApp"
        )
        .style.display=
        "block";

    }catch{

        showToast(
            "Gagal cek auth"
        );

    }

}