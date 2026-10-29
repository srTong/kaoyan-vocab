// Auth0 配置
const AUTH0_CONFIG = {
    domain: 'YOUR_AUTH0_DOMAIN', // 替换为你的 Auth0 域名，例如：dev-xxx.us.auth0.com
    clientId: 'YOUR_AUTH0_CLIENT_ID', // 替换为你的 Auth0 客户端 ID
    audience: 'https://YOUR_AUTH0_DOMAIN/userinfo', // 用户信息 API
    redirectUri: window.location.origin + window.location.pathname,
    scope: 'openid profile email'
};

// 全局用户状态
let currentUser = null;
let auth0Client = null;

// 初始化 Auth0
async function initAuth0() {
    try {
        auth0Client = await createAuth0Client({
            domain: AUTH0_CONFIG.domain,
            client_id: AUTH0_CONFIG.clientId,
            redirect_uri: AUTH0_CONFIG.redirectUri
        });

        // 检查是否从登录回调返回
        if (window.location.search.includes('code=') && window.location.search.includes('state=')) {
            await auth0Client.handleRedirectCallback();
            window.history.replaceState({}, document.title, window.location.pathname);
        }

        // 检查用户是否已登录
        const isAuthenticated = await auth0Client.isAuthenticated();
        if (isAuthenticated) {
            currentUser = await auth0Client.getUser();
            console.log('用户已登录:', currentUser);
            updateUIForLoggedInUser();
        } else {
            console.log('用户未登录');
            updateUIForLoggedOutUser();
        }
    } catch (error) {
        console.error('Auth0 初始化失败:', error);
        updateUIForLoggedOutUser();
    }
}

// 登录
async function login() {
    try {
        await auth0Client.loginWithRedirect({
            redirect_uri: AUTH0_CONFIG.redirectUri,
            scope: AUTH0_CONFIG.scope
        });
    } catch (error) {
        console.error('登录失败:', error);
        alert('登录失败，请重试');
    }
}

// 登出
function logout() {
    auth0Client.logout({
        returnTo: window.location.origin
    });
}

// 更新 UI - 已登录状态
function updateUIForLoggedInUser() {
    const loginBtn = document.getElementById('loginBtn');
    const userInfo = document.getElementById('userInfo');
    const userName = document.getElementById('userName');
    const userAvatar = document.getElementById('userAvatar');

    if (loginBtn) loginBtn.style.display = 'none';
    if (userInfo) {
        userInfo.style.display = 'flex';
        if (userName) userName.textContent = currentUser.name || currentUser.email;
        if (userAvatar) {
            userAvatar.src = currentUser.picture || 'https://via.placeholder.com/40';
            userAvatar.alt = currentUser.name || '用户头像';
        }
    }

    // 保存用户学习数据到本地存储
    saveUserData();
}

// 更新 UI - 未登录状态
function updateUIForLoggedOutUser() {
    const loginBtn = document.getElementById('loginBtn');
    const userInfo = document.getElementById('userInfo');

    if (loginBtn) loginBtn.style.display = 'inline-block';
    if (userInfo) userInfo.style.display = 'none';
}

// 保存用户数据（用于学习进度）
function saveUserData() {
    if (!currentUser) return;

    const userId = currentUser.sub;
    const userData = {
        userId: userId,
        lastLogin: new Date().toISOString(),
        progress: getLearningProgress()
    };

    localStorage.setItem(`user_${userId}`, JSON.stringify(userData));
}

// 获取学习进度
function getLearningProgress() {
    const progress = localStorage.getItem('learningProgress');
    return progress ? JSON.parse(progress) : {
        totalWords: 0,
        completedWords: [],
        quizScores: [],
        lastStudyDate: null
    };
}

// 更新学习进度
function updateLearningProgress(data) {
    const progress = getLearningProgress();
    Object.assign(progress, data);
    progress.lastStudyDate = new Date().toISOString();
    localStorage.setItem('learningProgress', JSON.stringify(progress));

    // 如果用户已登录，同步保存到用户数据
    if (currentUser) {
        saveUserData();
    }
}

// 页面加载时初始化
window.addEventListener('load', initAuth0);
