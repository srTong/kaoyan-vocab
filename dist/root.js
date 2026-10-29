// 词根详情页 JavaScript
let rootData = null;
const DATA_VERSION = '20261027-quality-gate-18';
let selectedScopes = [];

function hasUsableMeaning(word) {
    const meaning = (word.meaning || '').trim();
    return Boolean(meaning) && !/(待校对|待补充|相关的|有关的)/.test(meaning) &&
        !/(^|[；，\n])\s*(a|ad|adv|n|v|vt|vi|prep|conj)\./i.test(meaning) &&
        !/[A-Za-z]{3,}/.test(meaning);
}

// 获取 URL 参数
function getUrlParam(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

// 加载词根数据
async function loadRootData() {
    const rootName = getUrlParam('root');
    if (!rootName) {
        alert('参数错误');
        window.location.href = 'index.html';
        return;
    }

    try {
        // 先加载主数据文件找到词根
        const response = await fetch(`data/data.json?v=${DATA_VERSION}`);
        const appData = await response.json();
        
        // 找到对应的词根
        rootData = appData.roots.find(r => r.name === decodeURIComponent(rootName));
        
        if (!rootData) {
            alert('未找到该词根');
            window.location.href = 'index.html';
            return;
        }

        const scopeParam = getUrlParam('scopes');
        selectedScopes = scopeParam ? decodeURIComponent(scopeParam).split(',').filter(Boolean) : [];
        if (selectedScopes.length) {
            rootData = {...rootData, words: rootData.words.filter(word =>
                (word.scopes || []).some(scope => selectedScopes.includes(scope)))};
        }
        renderRootPage();
    } catch (error) {
        console.error('加载数据失败:', error);
        alert('加载数据失败，请刷新页面重试');
    }
}

// 渲染词根页面
function renderRootPage() {
    // 更新标题
    document.getElementById('rootName').textContent = rootData.name;
    document.getElementById('rootMeaning').textContent = rootData.meaning || '核心词根';

    // 渲染词源故事
    const storyContainer = document.getElementById('rootStory');
    if (storyContainer && rootData.story) {
        storyContainer.innerHTML = `
            <div class="story-box">
                <div class="story-title">词源故事</div>
                <div class="story-content">${rootData.story}</div>
            </div>
        `;
    }

    // 绑定练习按钮
    const practiceBtn = document.getElementById('practiceRootBtn');
    if (practiceBtn) {
        practiceBtn.addEventListener('click', () => {
            const rootName = encodeURIComponent(rootData.name);
            const scopeQuery = selectedScopes.length ? `&scopes=${encodeURIComponent(selectedScopes.join(','))}` : '';
            window.location.href = `practice.html?root=${rootName}${scopeQuery}`;
        });
    }

    // 渲染单词列表
    const container = document.getElementById('wordsList');
    
    if (rootData.words.length === 0) {
        container.innerHTML = '<p class="no-example">该词根下暂无单词</p>';
        return;
    }

    container.innerHTML = rootData.words.map(word => {
        const hasExample = word.example && word.example !== '';
        // 只显示有准确词根分解的单词（不包含"词根 →"这种通用解释）
        const hasEtymology = word.etymology && word.etymology !== '' && !word.etymology.includes('词根 →') && !word.etymology.includes('词根家族');
        
        return `
            <div class="word-card">
                <div class="word-header">
                    <div class="word-title">${word.word}${word.phonetic ? ` <span class="phonetic">${word.phonetic}</span>` : ''}</div>
                    <div class="word-meaning">${hasUsableMeaning(word) ? word.meaning : '释义待校对'}</div>
                </div>
                ${hasEtymology ? `
                    <div class="etymology-box">
                        <div class="etymology-label">词根分解</div>
                        <div class="etymology-text">${word.etymology}</div>
                    </div>
                ` : ''}
                ${hasExample ? `
                    <div class="example-box">
                        <div class="example-text">${word.example}</div>
                        <div class="example-source">—— ${word.source}</div>
                    </div>
                ` : `
                    <div class="no-example">暂无可靠例句；练习时将使用词义辨析题</div>
                `}
            </div>
        `;
    }).join('');
}

// 页面加载时初始化
window.addEventListener('DOMContentLoaded', loadRootData);
