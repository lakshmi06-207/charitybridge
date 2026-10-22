/* ============================================================
   CHARITYBRIDGE — COMMUNITY PAGE
   Liquid Glass Community Interaction
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    /* ========================================================
       SAFE COMMUNITY DATA
       ======================================================== */

    const dataElement = document.getElementById("community-data");

    let communityData = {};

    try {
        communityData = JSON.parse(
            dataElement ? dataElement.textContent : "{}"
        );
    } catch (error) {
        console.error("Community data error:", error);
        communityData = {};
    }

    const loggedInUserId = communityData.loggedInUserId || null;
    const isLoggedIn = Boolean(communityData.isLoggedIn);


    /* ========================================================
       ELEMENTS
       ======================================================== */

    const rudderToggle = document.getElementById("rudderToggle");
    const sidebarClose = document.getElementById("sidebarClose");
    const sidebar = document.getElementById("communitySidebar");

    const themeTopBtn = document.getElementById("themeTopBtn");
    const sidebarThemeBtn = document.getElementById("sidebarThemeBtn");
    const themePanel = document.getElementById("themePanel");
    const themePanelClose = document.getElementById("themePanelClose");

    const postForm = document.getElementById("communityPostForm");
    const postImage = document.getElementById("postImage");
    const selectedImageName = document.getElementById("selectedImageName");

    const loading = document.getElementById("communityLoading");

    const toast = document.getElementById("communityToast");
    const toastMessage = document.getElementById("toastMessage");
    const toastIcon = document.getElementById("toastIcon");


    /* ========================================================
       TOAST
       ======================================================== */

    let toastTimer = null;

    function showToast(message, type = "success") {
        if (!toast || !toastMessage) {
            return;
        }

        toastMessage.textContent = message;

        if (toastIcon) {
            if (type === "error") {
                toastIcon.textContent = "⚠";
            } else if (type === "info") {
                toastIcon.textContent = "ℹ";
            } else {
                toastIcon.textContent = "✓";
            }
        }

        toast.classList.add("show");

        clearTimeout(toastTimer);

        toastTimer = setTimeout(() => {
            toast.classList.remove("show");
        }, 3200);
    }


    /* ========================================================
       LOADING
       ======================================================== */

    function setLoading(show) {
        if (!loading) {
            return;
        }

        loading.hidden = !show;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    function openSidebar() {
        if (!sidebar) {
            return;
        }

        sidebar.classList.remove("closed");

        localStorage.setItem(
            "cbCommunitySidebarClosed",
            "false"
        );
    }

    function closeSidebar() {
        if (!sidebar) {
            return;
        }

        sidebar.classList.add("closed");

        localStorage.setItem(
            "cbCommunitySidebarClosed",
            "true"
        );
    }

    function toggleSidebar() {
        if (!sidebar) {
            return;
        }

        if (sidebar.classList.contains("closed")) {
            openSidebar();
        } else {
            closeSidebar();
        }
    }

    if (rudderToggle) {
        rudderToggle.addEventListener(
            "click",
            toggleSidebar
        );
    }

    if (sidebarClose) {
        sidebarClose.addEventListener(
            "click",
            closeSidebar
        );
    }

    const savedSidebarState = localStorage.getItem(
        "cbCommunitySidebarClosed"
    );

    if (savedSidebarState === "true") {
        sidebar?.classList.add("closed");
    }


    /* ========================================================
       THEME PANEL
       ======================================================== */

    function openThemePanel() {
        if (!themePanel) {
            return;
        }

        themePanel.classList.add("show");
    }

    function closeThemePanel() {
        if (!themePanel) {
            return;
        }

        themePanel.classList.remove("show");
    }

    if (themeTopBtn) {
        themeTopBtn.addEventListener(
            "click",
            openThemePanel
        );
    }

    if (sidebarThemeBtn) {
        sidebarThemeBtn.addEventListener(
            "click",
            openThemePanel
        );
    }

    if (themePanelClose) {
        themePanelClose.addEventListener(
            "click",
            closeThemePanel
        );
    }


    /* ========================================================
       THEME PRESETS
       ======================================================== */

    const themes = {
        aurora: {
            main: "#c86bff",
            secondary: "#7b61ff",
            accent: "#62e6ff"
        },

        ocean: {
            main: "#308cff",
            secondary: "#2459d9",
            accent: "#52e7e0"
        },

        pink: {
            main: "#ff70b7",
            secondary: "#d84f9b",
            accent: "#ffd0eb"
        },

        violet: {
            main: "#7b61ff",
            secondary: "#4e38bd",
            accent: "#d08cff"
        },

        gold: {
            main: "#d6a62b",
            secondary: "#9b7419",
            accent: "#fff0a8"
        }
    };


    function applyTheme(themeName) {
        const theme = themes[themeName];

        if (!theme) {
            return;
        }

        const root = document.documentElement;

        root.style.setProperty(
            "--theme-main",
            theme.main
        );

        root.style.setProperty(
            "--theme-secondary",
            theme.secondary
        );

        root.style.setProperty(
            "--theme-accent",
            theme.accent
        );

        localStorage.setItem(
            "cbCommunityTheme",
            themeName
        );

        document
            .querySelectorAll(".theme-option")
            .forEach(option => {
                option.classList.remove("active");

                if (
                    option.dataset.theme === themeName
                ) {
                    option.classList.add("active");
                }
            });
    }


    /* ========================================================
       THEME OPTIONS
       ======================================================== */

    document
        .querySelectorAll(".theme-option")
        .forEach(option => {

            option.addEventListener("click", () => {

                const themeName =
                    option.dataset.theme;

                if (!themeName) {
                    return;
                }

                applyTheme(themeName);

                showToast(
                    "Theme changed successfully.",
                    "success"
                );
            });
        });


    /* ========================================================
       CUSTOM THEME COLOR
       ======================================================== */

    const customThemeInput =
        document.getElementById("customThemeColor");

    const customThemeButton =
        document.getElementById("applyCustomTheme");

    function applyCustomTheme() {
        if (!customThemeInput) {
            return;
        }

        const color = customThemeInput.value;

        if (!color) {
            return;
        }

        const root = document.documentElement;

        root.style.setProperty(
            "--theme-main",
            color
        );

        root.style.setProperty(
            "--theme-secondary",
            color
        );

        root.style.setProperty(
            "--theme-accent",
            color
        );

        localStorage.setItem(
            "cbCommunityCustomTheme",
            color
        );

        document
            .querySelectorAll(".theme-option")
            .forEach(option => {
                option.classList.remove("active");
            });

        showToast(
            "Custom glass theme applied.",
            "success"
        );
    }

    if (customThemeButton) {
        customThemeButton.addEventListener(
            "click",
            applyCustomTheme
        );
    }


    /* ========================================================
       RESTORE SAVED THEME
       ======================================================== */

    const savedCustomTheme =
        localStorage.getItem(
            "cbCommunityCustomTheme"
        );

    const savedTheme =
        localStorage.getItem(
            "cbCommunityTheme"
        );

    if (savedCustomTheme) {

        const root = document.documentElement;

        root.style.setProperty(
            "--theme-main",
            savedCustomTheme
        );

        root.style.setProperty(
            "--theme-secondary",
            savedCustomTheme
        );

        root.style.setProperty(
            "--theme-accent",
            savedCustomTheme
        );

        if (customThemeInput) {
            customThemeInput.value =
                savedCustomTheme;
        }

    } else if (savedTheme && themes[savedTheme]) {

        applyTheme(savedTheme);

    } else {

        applyTheme("aurora");
    }


    /* ========================================================
       POST IMAGE NAME
       ======================================================== */

    if (postImage) {

        postImage.addEventListener(
            "change",
            () => {

                if (
                    postImage.files &&
                    postImage.files.length > 0
                ) {

                    const file =
                        postImage.files[0];

                    if (selectedImageName) {
                        selectedImageName.textContent =
                            file.name;
                    }

                } else {

                    if (selectedImageName) {
                        selectedImageName.textContent =
                            "";
                    }
                }
            }
        );
    }


    /* ========================================================
       CREATE POST
       ======================================================== */

    if (postForm) {

        postForm.addEventListener(
            "submit",
            async event => {

                event.preventDefault();

                if (!isLoggedIn) {
                    showToast(
                        "Please login to create a post.",
                        "error"
                    );
                    return;
                }

                const publishButton =
                    postForm.querySelector(
                        ".publishPostBtn"
                    );

                if (publishButton) {
                    publishButton.disabled = true;
                }

                setLoading(true);

                try {

                    const formData =
                        new FormData(postForm);

                    const response =
                        await fetch(
                            "/community/post/create",
                            {
                                method: "POST",
                                body: formData,
                                credentials: "same-origin"
                            }
                        );

                    let result = {};

                    try {
                        result =
                            await response.json();
                    } catch {
                        result = {};
                    }

                    if (
                        response.status === 401
                    ) {
                        showToast(
                            "Please login to create a post.",
                            "error"
                        );

                        return;
                    }

                    if (
                        !response.ok ||
                        !result.success
                    ) {

                        showToast(
                            result.message ||
                            "Unable to create the post.",
                            "error"
                        );

                        return;
                    }

                    showToast(
                        result.message ||
                        "Post published successfully.",
                        "success"
                    );

                    postForm.reset();

                    if (selectedImageName) {
                        selectedImageName.textContent =
                            "";
                    }

                    /*
                     * Reload so the newly-created post
                     * is loaded directly from MySQL.
                     */
                    setTimeout(() => {
                        window.location.reload();
                    }, 700);

                } catch (error) {

                    console.error(
                        "Create post error:",
                        error
                    );

                    showToast(
                        "Something went wrong while publishing.",
                        "error"
                    );

                } finally {

                    if (publishButton) {
                        publishButton.disabled = false;
                    }

                    setLoading(false);
                }
            }
        );
    }


    /* ========================================================
       SAFE IMAGE PATH
       ======================================================== */

    function getStaticImagePath(path) {

        if (!path) {
            return "";
        }

        const cleanPath =
            String(path)
                .replace(/^\/+/, "")
                .replace(/^static\//, "");

        return "/static/" + cleanPath;
    }


    /* ========================================================
       ESCAPE TEXT
       ======================================================== */

    function safeText(value) {
        return value === null ||
               value === undefined
            ? ""
            : String(value);
    }


    /* ========================================================
       COMMENTS
       ======================================================== */

    async function loadComments(
        postId,
        commentsArea,
        commentsList,
        commentsButton
    ) {

        try {

            commentsList.textContent = "";

            const loadingMessage =
                document.createElement("div");

            loadingMessage.className =
                "comments-loading";

            loadingMessage.textContent =
                "Loading comments...";

            commentsList.appendChild(
                loadingMessage
            );

            const response =
                await fetch(
                    `/community/post/${postId}/comments`,
                    {
                        method: "GET",
                        credentials: "same-origin"
                    }
                );

            const result =
                await response.json();

            if (!response.ok || !result.success) {
                throw new Error(
                    result.message ||
                    "Unable to load comments."
                );
            }

            commentsList.textContent = "";

            const comments =
                Array.isArray(result.comments)
                    ? result.comments
                    : [];

            if (comments.length === 0) {

                const empty =
                    document.createElement("div");

                empty.className =
                    "comments-empty";

                empty.textContent =
                    "No comments yet.";

                commentsList.appendChild(
                    empty
                );

            } else {

                comments.forEach(comment => {

                    const commentElement =
                        createCommentElement(
                            comment
                        );

                    commentsList.appendChild(
                        commentElement
                    );
                });
            }

            if (commentsButton) {

                const countElement =
                    commentsButton.querySelector(
                        ".comments-count-btn"
                    );

                if (countElement) {
                    countElement.textContent =
                        result.comment_count ??
                        comments.length;
                }
            }

            commentsArea.classList.add(
                "comments-open"
            );

        } catch (error) {

            console.error(
                "Comments error:",
                error
            );

            commentsList.textContent = "";

            const errorElement =
                document.createElement("div");

            errorElement.className =
                "comments-error";

            errorElement.textContent =
                "Unable to load comments.";

            commentsList.appendChild(
                errorElement
            );

            showToast(
                "Unable to load comments.",
                "error"
            );
        }
    }


    /* ========================================================
       CREATE COMMENT ELEMENT
       ======================================================== */

    function createCommentElement(comment) {

        const wrapper =
            document.createElement("div");

        wrapper.className =
            "community-comment";

        const header =
            document.createElement("div");

        header.className =
            "comment-header";

        const profileLink =
            document.createElement("a");

        profileLink.href =
            `/community/profile/${encodeURIComponent(
                comment.user_id
            )}`;

        profileLink.className =
            "comment-profile-link";

        const image =
            document.createElement("img");

        image.className =
            "comment-avatar";

        if (comment.profile_image) {

            image.src =
                getStaticImagePath(
                    comment.profile_image
                );

            image.alt =
                safeText(comment.name);

        } else {

            image.alt = "";

            image.classList.add(
                "no-profile-image"
            );
        }

        const name =
            document.createElement("span");

        name.className =
            "comment-user-name";

        name.textContent =
            safeText(comment.name) ||
            "Community Member";

        profileLink.appendChild(image);
        profileLink.appendChild(name);

        const role =
            document.createElement("span");

        role.className =
            "comment-user-role";

        role.textContent =
            safeText(comment.role);

        header.appendChild(
            profileLink
        );

        if (comment.role) {
            header.appendChild(role);
        }

        const text =
            document.createElement("div");

        text.className =
            "comment-text";

        text.textContent =
            safeText(comment.comment);

        const date =
            document.createElement("div");

        date.className =
            "comment-date";

        date.textContent =
            safeText(comment.created_at);

        wrapper.appendChild(header);
        wrapper.appendChild(text);
        wrapper.appendChild(date);

        return wrapper;
    }


    /* ========================================================
       ADD COMMENT
       ======================================================== */

    async function submitComment(form) {

        const postId =
            form.dataset.postId;

        const input =
            form.querySelector(
                'input[name="comment"], textarea[name="comment"]'
            );

        const submitButton =
            form.querySelector(
                "button[type='submit']"
            );

        if (!postId || !input) {
            return;
        }

        const comment =
            input.value.trim();

        if (!comment) {

            showToast(
                "Please write a comment.",
                "error"
            );

            return;
        }

        if (!isLoggedIn) {

            showToast(
                "Please login to comment.",
                "error"
            );

            return;
        }

        if (submitButton) {
            submitButton.disabled = true;
        }

        try {

            const response =
                await fetch(
                    `/community/post/${postId}/comment`,
                    {
                        method: "POST",
                        headers: {
                            "Content-Type":
                                "application/json"
                        },
                        credentials: "same-origin",
                        body: JSON.stringify({
                            comment: comment
                        })
                    }
                );

            let result = {};

            try {
                result =
                    await response.json();
            } catch {
                result = {};
            }

            if (
                response.status === 401
            ) {

                showToast(
                    "Please login to comment.",
                    "error"
                );

                return;
            }

            if (
                !response.ok ||
                !result.success
            ) {

                showToast(
                    result.message ||
                    "Unable to add comment.",
                    "error"
                );

                return;
            }

            input.value = "";

            const commentsArea =
                form.closest(
                    ".comments-area"
                );

            const commentsList =
                commentsArea
                    ?.querySelector(
                        ".comments-list"
                    );

            if (
                commentsList &&
                result.comment
            ) {

                const empty =
                    commentsList.querySelector(
                        ".comments-empty"
                    );

                if (empty) {
                    empty.remove();
                }

                const newComment =
                    createCommentElement(
                        result.comment
                    );

                commentsList.appendChild(
                    newComment
                );
            }

            const commentsButton =
                form.closest(
                    ".community-post-card"
                )?.querySelector(
                    '[data-action="comments"]'
                );

            if (commentsButton) {

                const countElement =
                    commentsButton.querySelector(
                        ".comments-count-btn"
                    );

                if (countElement) {

                    countElement.textContent =
                        result.comment_count ??
                        countElement.textContent;
                }
            }

            showToast(
                result.message ||
                "Comment added.",
                "success"
            );

        } catch (error) {

            console.error(
                "Comment error:",
                error
            );

            showToast(
                "Something went wrong while adding your comment.",
                "error"
            );

        } finally {

            if (submitButton) {
                submitButton.disabled = false;
            }
        }
    }


    /* ========================================================
       LIKE POST
       ======================================================== */

    async function toggleLike(button) {

        const postId =
            button.dataset.postId;

        if (!postId) {
            return;
        }

        if (!isLoggedIn) {

            showToast(
                "Please login to like a post.",
                "error"
            );

            return;
        }

        if (button.dataset.loading === "true") {
            return;
        }

        button.dataset.loading = "true";

        try {

            const response =
                await fetch(
                    `/community/post/${postId}/like`,
                    {
                        method: "POST",
                        credentials: "same-origin"
                    }
                );

            let result = {};

            try {
                result =
                    await response.json();
            } catch {
                result = {};
            }

            if (
                response.status === 401
            ) {

                showToast(
                    "Please login to like a post.",
                    "error"
                );

                return;
            }

            if (
                !response.ok ||
                !result.success
            ) {

                showToast(
                    result.message ||
                    "Unable to update like.",
                    "error"
                );

                return;
            }

            const card =
                button.closest(
                    ".community-post-card"
                );

            const count =
                card?.querySelector(
                    ".like-count"
                );

            if (count) {
                count.textContent =
                    result.like_count ?? 0;
            }

            if (result.liked) {

                button.classList.add(
                    "liked"
                );

                button.setAttribute(
                    "aria-pressed",
                    "true"
                );

                const icon =
                    button.querySelector(
                        ".like-icon"
                    );

                if (icon) {
                    icon.textContent = "♥";
                }

            } else {

                button.classList.remove(
                    "liked"
                );

                button.setAttribute(
                    "aria-pressed",
                    "false"
                );

                const icon =
                    button.querySelector(
                        ".like-icon"
                    );

                if (icon) {
                    icon.textContent = "♡";
                }
            }

        } catch (error) {

            console.error(
                "Like error:",
                error
            );

            showToast(
                "Unable to update the like.",
                "error"
            );

        } finally {

            button.dataset.loading = "false";
        }
    }


    /* ========================================================
       FOLLOW USER
       ======================================================== */

    async function toggleFollow(button) {

        const userId =
            button.dataset.userId;

        if (!userId) {
            return;
        }

        if (!isLoggedIn) {

            showToast(
                "Please login to follow members.",
                "error"
            );

            return;
        }

        if (button.dataset.loading === "true") {
            return;
        }

        button.dataset.loading = "true";

        try {

            const response =
                await fetch(
                    `/community/follow/${userId}`,
                    {
                        method: "POST",
                        credentials: "same-origin"
                    }
                );

            let result = {};

            try {
                result =
                    await response.json();
            } catch {
                result = {};
            }

            if (
                response.status === 401
            ) {

                showToast(
                    "Please login to follow members.",
                    "error"
                );

                return;
            }

            if (
                !response.ok ||
                !result.success
            ) {

                showToast(
                    result.message ||
                    "Unable to update follow status.",
                    "error"
                );

                return;
            }

            const following =
                Boolean(result.following);

            button.classList.toggle(
                "following",
                following
            );

            button.setAttribute(
                "aria-pressed",
                following ? "true" : "false"
            );

            button.textContent =
                following
                    ? "Following"
                    : "Follow";

            showToast(
                result.message ||
                (
                    following
                        ? "Following member."
                        : "Unfollowed member."
                ),
                "success"
            );

        } catch (error) {

            console.error(
                "Follow error:",
                error
            );

            showToast(
                "Unable to update follow status.",
                "error"
            );

        } finally {

            button.dataset.loading = "false";
        }
    }


    /* ========================================================
       MESSAGE BUTTON
       ======================================================== */

    function openMessage(button) {

        const userId =
            button.dataset.userId;

        if (!isLoggedIn) {

            showToast(
                "Please login to send a message.",
                "error"
            );

            return;
        }

        /*
         * No private-message route is assumed here.
         * This prevents a Flask BuildError / 404.
         */

        if (userId) {

            showToast(
                "Private chat will open here when Chat is connected.",
                "info"
            );

        } else {

            showToast(
                "Private chat is not connected yet.",
                "info"
            );
        }
    }


    /* ========================================================
       COMMENTS TOGGLE
       ======================================================== */

    async function toggleComments(button) {

        const card =
            button.closest(
                ".community-post-card"
            );

        if (!card) {
            return;
        }

        const commentsArea =
            card.querySelector(
                ".comments-area"
            );

        const commentsList =
            card.querySelector(
                ".comments-list"
            );

        if (!commentsArea || !commentsList) {
            return;
        }

        const isOpen =
            commentsArea.classList.contains(
                "comments-open"
            );

        if (isOpen) {

            commentsArea.classList.remove(
                "comments-open"
            );

            return;
        }

        await loadComments(
            button.dataset.postId,
            commentsArea,
            commentsList,
            button
        );
    }


    /* ========================================================
       EVENT DELEGATION
       ======================================================== */

    document.addEventListener(
        "click",
        event => {

            const actionElement =
                event.target.closest(
                    "[data-action]"
                );

            if (!actionElement) {
                return;
            }

            const action =
                actionElement.dataset.action;

            if (action === "like") {

                event.preventDefault();

                toggleLike(
                    actionElement
                );

                return;
            }

            if (action === "comments") {

                event.preventDefault();

                toggleComments(
                    actionElement
                );

                return;
            }

            if (action === "follow") {

                event.preventDefault();

                toggleFollow(
                    actionElement
                );

                return;
            }

            if (action === "message") {

                event.preventDefault();

                openMessage(
                    actionElement
                );

                return;
            }
        }
    );


    /* ========================================================
       COMMENT FORM EVENT DELEGATION
       ======================================================== */

    document.addEventListener(
        "submit",
        event => {

            const form =
                event.target.closest(
                    ".comment-form"
                );

            if (!form) {
                return;
            }

            event.preventDefault();

            submitComment(form);
        }
    );


    /* ========================================================
       ESCAPE KEY
       ======================================================== */

    document.addEventListener(
        "keydown",
        event => {

            if (event.key === "Escape") {

                closeThemePanel();
            }
        }
    );


    /* ========================================================
       CLICK OUTSIDE THEME PANEL
       ======================================================== */

    document.addEventListener(
        "click",
        event => {

            if (!themePanel) {
                return;
            }

            if (
                !themePanel.classList.contains(
                    "show"
                )
            ) {
                return;
            }

            const clickedInsidePanel =
                themePanel.contains(
                    event.target
                );

            const clickedThemeButton =
                themeTopBtn?.contains(
                    event.target
                ) ||
                sidebarThemeBtn?.contains(
                    event.target
                );

            if (
                !clickedInsidePanel &&
                !clickedThemeButton
            ) {
                closeThemePanel();
            }
        }
    );


    /* ========================================================
       PROFILE IMAGE FALLBACK
       ======================================================== */

    document
        .querySelectorAll(
            "img[data-profile-image]"
        )
        .forEach(image => {

            image.addEventListener(
                "error",
                () => {

                    image.style.display =
                        "none";
                }
            );
        });


    /* ========================================================
       FINISHED
       ======================================================== */

    console.log(
        "CharityBridge Community loaded.",
        {
            loggedInUserId:
                loggedInUserId,
            isLoggedIn:
                isLoggedIn,
            peopleConnected:
                communityData.peopleConnected ?? 0,
            totalUsers:
                communityData.totalUsers ?? 0,
            communityPosts:
                communityData.communityPostsCount ?? 0
        }
    );
});