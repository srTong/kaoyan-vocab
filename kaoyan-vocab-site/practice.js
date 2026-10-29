// 练习页面 JavaScript
let appData = null;
const DATA_VERSION = '20261027-quality-gate-18';
let questions = [];
let currentQuestionIndex = 0;
let score = 0;
let answered = false;
let currentRoot = null;
let selectedScopes = [];

// 获取 URL 参数
function getUrlParam(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

// 加载数据
async function loadData() {
    try {
        const response = await fetch(`data/data.json?v=${DATA_VERSION}`);
        appData = await response.json();
        const scopeParam = getUrlParam('scopes');
        selectedScopes = scopeParam ? decodeURIComponent(scopeParam).split(',').filter(Boolean) : [];
        
        // 检查是否指定了词根
        const rootParam = getUrlParam('root');
        if (rootParam) {
            currentRoot = decodeURIComponent(rootParam);
            document.querySelector('.subtitle').textContent = `练习词根: ${currentRoot}`;
        } else {
            document.querySelector('.subtitle').textContent = '根据语境或释义选择正确的单词';
        }
        
        generateQuestions();
        renderQuestion();
    } catch (error) {
        console.error('加载数据失败:', error);
        alert('加载数据失败，请刷新页面重试');
    }
}

function hasUsableContextExample(word) {
    if (!word.example || word.source?.startsWith('模拟例句') || word.source?.startsWith('通用例句')) {
        return false;
    }
    // 例句必须是真实、语义相容的语境；历史自动模板即使能匹配目标词，
    // 也不能拿来挖空，否则会把错误搭配显示成正确答案。
    const unsafePatterns = [
        'The article discusses',
        'The study links',
        'The evidence shows why',
        'Researchers observed',
        'The approach seems',
        'Researchers described the policy as',
        'The evidence points to',
        'The change made the system more',
        'The policy was implemented',
        'The change occurred',
        'The results were reported',
        'The researchers tried to',
        'The researchers assessed the evidence',
        'The result was',
        'includes the word'
    ];
    const lowered = word.example.toLowerCase();
    if (unsafePatterns.some(pattern => lowered.includes(pattern.toLowerCase()))) {
        return false;
    }
    // 元语言句可作为词卡保底，但不应作为“根据句意”题的语境。
    if (/\b(the term|the sentence uses|the root|the verb)\b/i.test(word.example)) {
        return false;
    }
    const variants = getWordVariants(word.word).sort((a, b) => b.length - a.length);
    return variants.some(variant => new RegExp(`\\b${variant}\\b`, 'i').test(word.example)) ||
        new RegExp(`\\b${word.word}[a-z]*\\b`, 'i').test(word.example);
}

function hasUsableMeaning(word) {
    const meaning = (word.meaning || '').trim();
    return Boolean(meaning) && !/(待校对|待补充|相关的|有关的)/.test(meaning) &&
        !/(^|[；，\n])\s*(a|ad|adv|n|v|vt|vi|prep|conj)\./i.test(meaning) &&
        !/[A-Za-z]{3,}/.test(meaning);
}

// 生成练习题：可靠例句优先；自动模板只用于词义题，绝不再作为完形语境。
function generateQuestions() {
    const candidates = [];
    
    appData.roots.forEach(root => {
        // 如果指定了词根，只收集该词根的单词
        if (currentRoot && root.name !== currentRoot) {
            return;
        }
        
        root.words.forEach(word => {
            if (selectedScopes.length && !(word.scopes || []).some(scope => selectedScopes.includes(scope))) {
                return;
            }
            if (word.word && hasUsableMeaning(word)) {
                candidates.push({
                    ...word,
                    root: root.name
                });
            }
        });
    });

    const total = Math.min(10, candidates.length);
    const contextQuestions = shuffledCopy(candidates.filter(hasUsableContextExample))
        .map(word => ({ ...word, quizMode: 'context' }));
    const definitionQuestions = shuffledCopy(candidates.filter(word => !hasUsableContextExample(word)))
        .map(word => ({ ...word, quizMode: 'definition' }));
    questions = contextQuestions.slice(0, total);
    if (questions.length < total) {
        questions.push(...definitionQuestions.slice(0, total - questions.length));
    }
    questions = shuffledCopy(questions);

    document.getElementById('totalQuestions').textContent = questions.length;
}

// 渲染当前题目
function renderQuestion() {
    if (currentQuestionIndex >= questions.length) {
        showResults();
        return;
    }

    answered = false;
    const question = questions[currentQuestionIndex];
    
    // 更新进度
    document.getElementById('currentQuestion').textContent = currentQuestionIndex + 1;
    document.getElementById('progressFill').style.width = 
        `${((currentQuestionIndex) / questions.length) * 100}%`;

    const sentenceElement = document.getElementById('exampleSentence');
    const sourceElement = document.getElementById('sourceInfo');
    if (question.quizMode === 'context') {
        sentenceElement.innerHTML = createBlankSentence(question.example, question.word);
        sourceElement.textContent = `${question.phonetic ? `音标: ${question.phonetic} · ` : ''}来源: ${question.source}`;
    } else {
        sentenceElement.textContent = `请选择与“${question.meaning}”意思最相符的单词。`;
        sourceElement.textContent = `${question.phonetic ? `音标: ${question.phonetic} · ` : ''}题型: 词义辨析`;
    }

    // 生成选项
    const options = generateOptions(question);
    renderOptions(options, question.word, question.root);

    // 隐藏反馈和按钮
    document.getElementById('feedback').className = 'feedback';
    document.getElementById('feedback').textContent = '';
    document.getElementById('nextBtn').style.display = 'none';
}

// 创建挖空句子
function createBlankSentence(sentence, targetWord) {
    // 清理句子中的特殊字符，防止 HTML 注入
    let cleanSentence = sentence
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    
    // 生成目标单词的词形变体（匹配例句中可能出现的不同形态）
    const variants = getWordVariants(targetWord);
    
    // 按长度从长到短排序，优先匹配更具体的变体（如 dictated 优先于 dictate）
    variants.sort((a, b) => b.length - a.length);
    
    // 尝试匹配任意变体
    for (const variant of variants) {
        const regex = new RegExp(`\\b${variant}\\b`, 'gi');
        if (regex.test(cleanSentence)) {
            return cleanSentence.replace(regex, '<span class="blank">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>');
        }
    }
    
    // 如果精确匹配失败，尝试模糊匹配（例句中包含目标词的前缀）
    const stemRegex = new RegExp(`\\b${targetWord}[a-z]*\\b`, 'gi');
    if (stemRegex.test(cleanSentence)) {
        return cleanSentence.replace(stemRegex, '<span class="blank">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</span>');
    }
    
    // 最终兜底：直接返回原句（不挖空）
    return cleanSentence;
}

// 生成单词的词形变体
function getWordVariants(word) {
    const variants = [word];
    const w = word.toLowerCase();
    
    // 常见词形变化规则
    const suffixes = ['s', 'es', 'ed', 'd', 'ing', 'ly', 'er', 'est', 'ment', 'tion', 'sion', 'ness', 'able', 'ible', 'ful', 'less', 'ous', 'ive', 'al', 'ial'];
    
    // 直接加后缀
    suffixes.forEach(suffix => {
        variants.push(w + suffix);
    });
    
    // 特殊变形规则
    // 以 e 结尾的：去掉 e 再加
    if (w.endsWith('e')) {
        const stem = w.slice(0, -1);
        variants.push(stem + 'd');
        variants.push(stem + 'ing');
        suffixes.forEach(suffix => {
            variants.push(stem + suffix);
        });
    }
    
    // 以 y 结尾的：变 y 为 i
    if (w.endsWith('y') && w.length > 2) {
        const stem = w.slice(0, -1) + 'i';
        variants.push(stem + 'ed');
        variants.push(stem + 'es');
        variants.push(stem + 'ly');
        variants.push(stem + 'ness');
        variants.push(stem + 'able');
    }
    
    // 双写末尾辅音字母
    if (w.length >= 3 && !'aeiou'.includes(w[w.length - 1]) && 'aeiou'.includes(w[w.length - 2])) {
        const doubled = w + w[w.length - 1];
        variants.push(doubled + 'ed');
        variants.push(doubled + 'ing');
    }
    
    // 去重
    return [...new Set(variants)];
}

function isInSelectedScope(word) {
    return !selectedScopes.length || (word.scopes || []).some(scope => selectedScopes.includes(scope));
}

function shuffledCopy(items) {
    const result = [...items];
    for (let i = result.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [result[i], result[j]] = [result[j], result[i]];
    }
    return result;
}

// 生成选项：词根专项练习必须优先使用同词根词汇作为干扰项。
function generateOptions(question) {
    const correctWord = question.word;
    const correctRoot = question.root;
    const options = [correctWord];
    const wordLength = correctWord.length;
    const currentRootData = appData.roots.find(r => r.name === correctRoot);
    const seen = new Set([correctWord.toLowerCase()]);

    const addPool = (words) => {
        for (const word of shuffledCopy(words)) {
            const key = word.toLowerCase();
            if (options.length >= 4) break;
            if (!seen.has(key)) {
                seen.add(key);
                options.push(word);
            }
        }
    };

    const sameRootEntries = currentRootData
        ? currentRootData.words.filter(w => hasUsableMeaning(w) && w.word && w.word.toLowerCase() !== correctWord.toLowerCase())
        : [];

    // 1. 当前 scope 内的同词根词；这是正常情况下唯一会使用的干扰项来源。
    addPool(sameRootEntries.filter(isInSelectedScope).map(w => w.word));

    // 2. 如果当前 scope 中不足四个选项，仍优先从该词根的其他 scope 补齐。
    if (options.length < 4 && currentRoot) {
        addPool(sameRootEntries.map(w => w.word));
    }

    // 3. 极小词族才使用含义相近的其他词根，并继续遵守 scope 筛选。
    const similarRootWords = [];
    if (currentRootData && currentRootData.meaning) {
        const currentMeaningParts = currentRootData.meaning.split(/[,，、]/).map(s => s.trim());
        appData.roots.forEach(root => {
            if (root.name === correctRoot || !root.meaning) return;
            const rootMeaningParts = root.meaning.split(/[,，、]/).map(s => s.trim());
            // 检查是否有共同含义
            const hasOverlap = currentMeaningParts.some(m => 
                rootMeaningParts.some(rm => rm.includes(m) || m.includes(rm))
            );
            if (hasOverlap) {
                root.words.forEach(word => {
                    if (word.word && hasUsableMeaning(word) && isInSelectedScope(word) &&
                        word.word.toLowerCase() !== correctWord.toLowerCase()) {
                        similarRootWords.push(word.word);
                    }
                });
            }
        });
    }
    addPool(similarRootWords);

    // 4. 最终兜底：从当前 scope 选择长度接近的词，只用于不足四词的极小词族。
    if (options.length < 4) {
        const fallbackWords = appData.roots.flatMap(root =>
            root.words.filter(word => word.word && hasUsableMeaning(word) && isInSelectedScope(word)).map(word => word.word)
        );
        const sorted = fallbackWords
            .filter(word => !seen.has(word.toLowerCase()))
            .sort((a, b) => Math.abs(a.length - wordLength) - Math.abs(b.length - wordLength));
        addPool(sorted.slice(0, 100));
    }

    return shuffledCopy(options);
}

function findOptionRecord(optionWord, preferredRoot) {
    const key = optionWord.toLowerCase();
    const root = appData.roots.find(item => item.name === preferredRoot);
    const preferred = root && root.words.find(word => word.word.toLowerCase() === key);
    if (preferred) return { word: preferred, root };

    for (const item of appData.roots) {
        const match = item.words.find(word => word.word.toLowerCase() === key);
        if (match) return { word: match, root: item };
    }
    return null;
}

// 渲染选项；中文释义在作答后统一揭示。
function renderOptions(options, correctWord, preferredRoot) {
    const container = document.getElementById('options');
    container.innerHTML = '';

    options.forEach(option => {
        const record = findOptionRecord(option, preferredRoot);
        const button = document.createElement('button');
        button.className = 'option-btn';
        button.dataset.word = option;

        const wordLabel = document.createElement('span');
        wordLabel.className = 'option-word';
        wordLabel.textContent = option;

        const meaningLabel = document.createElement('span');
        meaningLabel.className = 'option-detail option-meaning';
        meaningLabel.textContent = `中文：${record?.word.meaning || '释义待补充'}`;
        meaningLabel.hidden = true;
        meaningLabel.setAttribute('aria-hidden', 'true');
        meaningLabel.style.display = 'none';

        const rootLabel = document.createElement('span');
        rootLabel.className = 'option-detail option-root';
        rootLabel.textContent = record
            ? `构词：${record.word.etymology || `${record.root.name}（${record.root.meaning || '释义待补充'}）`}`
            : '构词：待补充';
        rootLabel.hidden = true;
        rootLabel.setAttribute('aria-hidden', 'true');
        rootLabel.style.display = 'none';

        button.append(wordLabel, meaningLabel, rootLabel);
        container.appendChild(button);
    });

    // 添加点击事件
    container.querySelectorAll('.option-btn').forEach(btn => {
        btn.addEventListener('click', () => handleAnswer(btn, correctWord));
    });
}

// 处理答案
function handleAnswer(selectedBtn, correctWord) {
    if (answered) return;
    answered = true;

    const selectedWord = selectedBtn.dataset.word;
    const isCorrect = selectedWord === correctWord;

    // 标记正确/错误
    if (isCorrect) {
        selectedBtn.classList.add('correct');
        score++;
        document.getElementById('score').textContent = score;
        document.getElementById('feedback').className = 'feedback correct';
        document.getElementById('feedback').textContent = '✓ 正确！';
    } else {
        selectedBtn.classList.add('wrong');
        // 显示正确答案
        document.querySelectorAll('.option-btn').forEach(btn => {
            if (btn.dataset.word === correctWord) {
                btn.classList.add('correct');
            }
        });
        document.getElementById('feedback').className = 'feedback wrong';
        document.getElementById('feedback').textContent = `✗ 正确答案是: ${correctWord}`;
    }

    // 禁用所有选项
    document.querySelectorAll('.option-btn').forEach(btn => {
        btn.classList.add('disabled');
        btn.classList.add('revealed');
        btn.querySelectorAll('.option-detail').forEach(detail => {
            detail.hidden = false;
            detail.setAttribute('aria-hidden', 'false');
            detail.style.removeProperty('display');
        });
    });

    // 填充空白
    const blank = document.querySelector('.blank');
    if (blank) {
        blank.textContent = correctWord;
        blank.style.color = isCorrect ? '#28a745' : '#dc3545';
    }

    // 显示下一题按钮
    document.getElementById('nextBtn').style.display = 'inline-block';
}

// 保存测验结果
function saveQuizResults(correct, total, percentage) {
    // 获取当前进度
    const progress = typeof getLearningProgress === 'function' ? getLearningProgress() : {
        totalWords: 0,
        completedWords: [],
        quizScores: [],
        lastStudyDate: null
    };
    
    // 记录本次测验
    progress.quizScores.push({
        date: new Date().toISOString(),
        correct: correct,
        total: total,
        percentage: percentage,
        words: questions.map(q => q.word)
    });
    
    // 更新已完成的单词
    questions.forEach(q => {
        if (!progress.completedWords.includes(q.word)) {
            progress.completedWords.push(q.word);
        }
    });
    
    progress.totalWords = progress.completedWords.length;
    progress.lastStudyDate = new Date().toISOString();
    
    // 保存到本地存储
    localStorage.setItem('learningProgress', JSON.stringify(progress));
    
    // 如果用户已登录，同步保存
    if (typeof updateLearningProgress === 'function') {
        updateLearningProgress(progress);
    }
    
    console.log('学习进度已保存:', progress);
}

// 显示结果
function showResults() {
    const percentage = Math.round((score / questions.length) * 100);
    
    document.getElementById('progressFill').style.width = '100%';
    
    // 保存学习进度
    saveQuizResults(score, questions.length, percentage);
    
    const container = document.querySelector('.question-card');
    container.innerHTML = `
        <div style="text-align: center; padding: 40px;">
            <h2 style="font-size: 2em; margin-bottom: 20px;">练习完成！</h2>
            <div style="font-size: 3em; color: #667eea; margin: 30px 0;">
                ${score} / ${questions.length}
            </div>
            <div style="font-size: 1.5em; color: #666; margin-bottom: 30px;">
                正确率: ${percentage}%
            </div>
            <div style="font-size: 1.2em; color: #999;">
                ${percentage >= 80 ? '🎉 太棒了！继续保持！' : 
                  percentage >= 60 ? '👍 不错，继续加油！' : 
                  '💪 多练习几次，你会进步的！'}
            </div>
        </div>
    `;

    document.getElementById('nextBtn').style.display = 'none';
    document.getElementById('restartBtn').style.display = 'inline-block';
}

// 下一题
document.getElementById('nextBtn').addEventListener('click', () => {
    currentQuestionIndex++;
    renderQuestion();
});

// 重新开始
document.getElementById('restartBtn').addEventListener('click', () => {
    currentQuestionIndex = 0;
    score = 0;
    document.getElementById('score').textContent = 0;
    generateQuestions();
    
    // 重新渲染题目卡片
    const container = document.querySelector('.question-card');
    container.innerHTML = `
        <div class="example-sentence" id="exampleSentence"></div>
        <div class="source-info" id="sourceInfo"></div>
        <div class="options" id="options"></div>
        <div class="feedback" id="feedback"></div>
    `;
    
    renderQuestion();
});

// 页面加载时初始化
window.addEventListener('DOMContentLoaded', loadData);
