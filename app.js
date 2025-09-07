// 全局变量
let currentPosition = null;
let currentHeading = 0;
let currentLanguage = 'zh';

// 多语言翻译函数（增强版，支持嵌套键值和变量替换）
function t(key, options = {}) {
    const translations = window.translations || {};
    const langTranslations = translations[currentLanguage] || translations['zh'] || {};
    
    let value = langTranslations;
    const keys = key.split('.');
    
    for (const k of keys) {
        if (value && typeof value === 'object' && k in value) {
            value = value[k];
        } else {
            return key; // 返回key本身作为fallback
        }
    }
    
    if (typeof value === 'string') {
        // 变量替换
        if (options) {
            return value.replace(/\{\{(\w+)\}\}/g, (match, varName) => {
                return options[varName] || match;
            });
        }
        return value;
    }
    
    return key;
}

// API配置 - 由index.html中的getAPIBaseURL()函数动态设置

// Google街景相关变量
let streetViewPanorama = null;
let streetViewService = null;
let currentStreetViewLocation = null;
let isStreetViewFullscreen = false;
let settings = {
    segmentDistance: 10,
    timeMode: 'present',
    speed: 120,
    dataSource: 'real'  // 只使用真实数据
};

// 场景管理状态
let sceneManagement = {
    allScenes: [],          // 所有场景列表
    selectedScenes: [],     // 用户选中的场景
    rejectedScenes: [],     // 用户划掉的场景
    isSelectionMode: false, // 是否处于选择模式
    // 🆕 跟踪当前正在确认到达的场景，用于处理"返回"按钮
    currentlyVisitingScene: null
};

// 旅程管理状态
let journeyManagement = {
    currentJourneyId: null,     // 当前旅程ID
    isJourneyActive: false,     // 是否有活跃旅程
    startLocation: null,        // 起始位置
    visitedScenes: [],          // 已访问的场景
    totalDistance: 0,           // 总行程距离
    historyScenes: []           // 历史场景显示数据
};

// 日志系统
class Logger {
    constructor() {
        this.logs = [];
        this.maxLogs = 100;
    }
    
    log(message, type = 'info') {
        const timestamp = new Date().toLocaleTimeString();
        // 支持翻译键值
        const translatedMessage = typeof message === 'string' && message.includes('.') ? t(message) : message;
        const logEntry = {
            timestamp,
            message: translatedMessage,
            type,
            id: Date.now()
        };
        
        this.logs.unshift(logEntry);
        if (this.logs.length > this.maxLogs) {
            this.logs.pop();
        }
        
        this.displayLog(logEntry);
        console.log(`[${timestamp}] ${type.toUpperCase()}: ${translatedMessage}`);
    }
    
    info(message) { this.log(message, 'info'); }
    success(message) { this.log(message, 'success'); }
    warning(message) { this.log(message, 'warning'); }
    error(message) { this.log(message, 'error'); }
    
    displayLog(logEntry) {
        const container = document.getElementById('logContainer');
        if (!container) return;
        
        const logElement = document.createElement('div');
        logElement.className = `log-entry ${logEntry.type}`;
        logElement.innerHTML = `
            <span class="log-timestamp">[${logEntry.timestamp}]</span>
            <span class="log-message">${logEntry.message}</span>
        `;
        
        container.insertBefore(logElement, container.firstChild);
        
        // 限制显示的日志数量
        const entries = container.querySelectorAll('.log-entry');
        if (entries.length > 50) {
            entries[entries.length - 1].remove();
        }
    }
    
    clear() {
        this.logs = [];
        const container = document.getElementById('logContainer');
        if (container) {
            container.innerHTML = '';
        }
        console.clear();
    }
}

const logger = new Logger();

// 初始化应用
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

async function initializeApp() {
    logger.info('system.appStart');
    logger.info('system.initializing');
    
    // 检查浏览器支持
    if (!checkBrowserSupport()) {
        const errorMsg = t('system.browserNotSupported');
        logger.error(errorMsg);
        showError(errorMsg);
        return;
    }
    
    logger.success('system.browserCheckPassed');
    
    // 请求权限并获取位置
    await requestPermissions();
    
    // 初始化传感器
    initializeCompass();
    
    // 初始化点击指南针功能
    initializeCompassClick();
    
    // 初始化城市数据库
    await initializeCityDatabase();
    
    // 获取初始位置
    refreshLocation();
    
    logger.success('system.initializationComplete');
}

// 初始化点击指南针功能
function initializeCompassClick() {
    const compass = document.getElementById('compass');
    if (compass) {
        // 添加点击事件
        compass.style.cursor = 'pointer';
        compass.addEventListener('click', function(event) {
            const rect = compass.getBoundingClientRect();
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            
            // 计算点击位置相对于中心的角度
            const x = event.clientX - centerX;
            const y = event.clientY - centerY;
            
            // 计算角度（从北开始顺时针）
            let angle = Math.atan2(x, -y) * (180 / Math.PI);
            if (angle < 0) angle += 360;
            
            // 设置新的方向
            currentHeading = Math.round(angle);
            updateCompassDisplay(currentHeading);
            logger.success(`通过点击设置方向: ${currentHeading}°`);
            
            // 隐藏手动输入框（如果存在）
            const manualInput = document.querySelector('.manual-heading-input');
            if (manualInput) {
                manualInput.style.display = 'none';
            }
        });
        
        // 添加鼠标悬停提示
        compass.title = t('compass.manualInput.clickToSet');
    }
}

// 启用手动输入方向功能
function enableManualHeadingInput() {
    logger.info('启用手动方向输入模式');
    
    // 查找合适的位置插入手动输入控件
    const statusDisplay = document.querySelector('.status-display');
    const compassContainer = document.querySelector('.compass-container');
    const targetElement = compassContainer || statusDisplay;
    
    if (targetElement && !document.querySelector('.manual-heading-input')) {
        const manualInput = document.createElement('div');
        manualInput.className = 'manual-heading-input';
        manualInput.style.cssText = 'background: #fff3cd; border: 1px solid #ffecc0; border-radius: 8px; padding: 15px; margin: 10px 0;';
        manualInput.innerHTML = `
            <p style="color: #856404; margin: 0 0 10px 0; font-weight: bold;">📍 ${t('compass.manualInput.title')}</p>
            <p style="color: #856404; margin: 0 0 10px 0;">${t('compass.manualInput.instruction')}</p>
            <div style="display: flex; align-items: center; gap: 10px;">
                <input type="number" id="manualHeading" min="0" max="359" value="${currentHeading || 0}" 
                       placeholder="${t('compass.manualInput.placeholder')}" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 120px;">
                <button onclick="setManualHeading()" style="padding: 8px 15px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">${t('compass.manualInput.button')}</button>
            </div>
            <p style="font-size: 12px; color: #666; margin: 10px 0 0 0;">💡 ${t('compass.manualInput.hint')}</p>
        `;
        targetElement.parentNode.insertBefore(manualInput, targetElement.nextSibling);
    }
}

// 设置手动方向
window.setManualHeading = function() {
    const input = document.getElementById('manualHeading');
    if (input) {
        const heading = parseInt(input.value);
        if (!isNaN(heading) && heading >= 0 && heading <= 359) {
            currentHeading = heading;
            updateCompassDisplay(heading);
            logger.success(`手动设置方向: ${heading}°`);
            
            // 隐藏输入框
            const manualInput = document.querySelector('.manual-heading-input');
            if (manualInput) {
                manualInput.style.display = 'none';
            }
        } else {
            logger.error('compass.invalidAngle');
        }
    }
}

function checkBrowserSupport() {
    return 'geolocation' in navigator && 
           'DeviceOrientationEvent' in window &&
           typeof fetch !== 'undefined';
}

async function requestPermissions() {
    try {
        // 请求地理位置权限
        if ('permissions' in navigator) {
            const geoPermission = await navigator.permissions.query({name: 'geolocation'});
            logger.info(t('location.permissionStatus', {status: geoPermission.state}));
        }
        
        // 请求设备方向权限 (iOS 13+)
        if (typeof DeviceOrientationEvent.requestPermission === 'function') {
            logger.info('compass.iosPermissionRequired');
            try {
            const permission = await DeviceOrientationEvent.requestPermission();
                logger.info(t('compass.deviceOrientationPermission', {permission: permission}));
            if (permission !== 'granted') {
                    logger.warning('compass.permissionRequired');
                showError(t('compass.permissionRequired'));
                }
            } catch (error) {
                logger.error(t('compass.permissionRequestFailed', {error: error.message}));
            }
        } else {
            logger.info('compass.deviceSupported');
        }
    } catch (error) {
        logger.error(t('compass.permissionRequestFailedGeneric', {error: error.message}));
    }
}

function initializeCompass() {
    logger.info('compass.initializing');
    
    // 监听设备方向变化
    if (window.DeviceOrientationEvent) {
        logger.info('compass.deviceOrientationSupported');
        
        // 添加deviceorientation事件监听
        window.addEventListener('deviceorientation', function(event) {
            if (event.alpha !== null || event.webkitCompassHeading !== undefined) {
                logger.success('compass.orientationEventTriggered');
                handleOrientation(event);
            } else {
                logger.warning('compass.orientationEventNoData');
            }
        }, true);
        
        // 添加deviceorientationabsolute事件监听（某些设备）
        window.addEventListener('deviceorientationabsolute', function(event) {
            if (event.absolute && event.alpha !== null) {
                logger.info('compass.absoluteOrientationEvent');
                handleOrientation(event);
            }
        }, true);
        
        // 测试是否能获取方向
        setTimeout(() => {
            if (currentHeading === null || currentHeading === undefined) {
                logger.warning('compass.noOrientationData');
                // 提供手动输入方向的选项
                enableManualHeadingInput();
            } else if (currentHeading === 0) {
                logger.info('compass.northDetected');
            }
        }, 1000);  // 缩短到1秒
    } else {
        logger.error('compass.deviceNotSupported');
        showError(t('compass.deviceNotSupported'));
        enableManualHeadingInput();
    }
}

function handleOrientation(event) {
    // 获取指南针方向
    let heading = event.alpha;
    
    // iOS Safari 使用 webkitCompassHeading
    if (event.webkitCompassHeading) {
        heading = event.webkitCompassHeading;
    }
    
    if (heading !== null) {
        // 标准化角度 (0-360)
        heading = (360 - heading) % 360;
        currentHeading = heading;
        updateCompassDisplay(heading);
    }
}

function updateCompassDisplay(heading) {
    const compassNeedle = document.getElementById('compassNeedle');
    const compassDirection = document.getElementById('compassDirection');
    const directionText = document.getElementById('directionText');
    
    if (compassNeedle) {
        // 围绕中心旋转指南针
        compassNeedle.style.transform = `translate(-50%, -50%) rotate(${heading}deg)`;
    }
    
    if (compassDirection) {
        compassDirection.textContent = `${Math.round(heading)}°`;
    }
    
    if (directionText) {
        directionText.textContent = getDirectionText(heading);
    }
    
    logger.info(t('compass.directionUpdated', {heading: Math.round(heading), direction: getDirectionText(heading)}));
}

function getDirectionText(heading) {
    const directions = [
        { name: t('compass.directions.north'), min: 0, max: 22.5 },
        { name: t('compass.directions.northeast'), min: 22.5, max: 67.5 },
        { name: t('compass.directions.east'), min: 67.5, max: 112.5 },
        { name: t('compass.directions.southeast'), min: 112.5, max: 157.5 },
        { name: t('compass.directions.south'), min: 157.5, max: 202.5 },
        { name: t('compass.directions.southwest'), min: 202.5, max: 247.5 },
        { name: t('compass.directions.west'), min: 247.5, max: 292.5 },
        { name: t('compass.directions.northwest'), min: 292.5, max: 337.5 },
        { name: t('compass.directions.north'), min: 337.5, max: 360 }
    ];
    
    for (const dir of directions) {
        if (heading >= dir.min && heading < dir.max) {
            return dir.name;
        }
    }
    return t('compass.directions.north');
}

function refreshLocation() {
    logger.info('location.gettingLocation');
    
    const locationElement = document.getElementById('currentLocation');
    const coordinatesElement = document.getElementById('coordinates');
    const accuracyElement = document.getElementById('accuracy');
    
    locationElement.textContent = t('system.getting');
    coordinatesElement.textContent = t('system.getting');
    accuracyElement.textContent = t('system.getting');
    
    // 检查浏览器支持
    if (!navigator.geolocation) {
        const errorMsg = t('location.browserNotSupported');
        logger.error(errorMsg);
        showError(errorMsg);
        showManualLocationInput();
        return;
    }
    
    // 检查是否为安全上下文（HTTPS 或 localhost）
    const isSecureContext = window.isSecureContext || location.protocol === 'https:' || location.hostname === 'localhost';
    if (!isSecureContext) {
        logger.warning('⚠️ 非安全上下文，地理位置功能可能受限');
        showError('⚠️ 建议使用 HTTPS 或 localhost 访问以获得最佳体验');
    }
    
    // 首先检查权限状态
    if ('permissions' in navigator) {
        navigator.permissions.query({name: 'geolocation'}).then(function(permissionStatus) {
            logger.info(`地理位置权限状态: ${permissionStatus.state}`);
            
            if (permissionStatus.state === 'denied') {
                logger.error('❌ 地理位置权限被拒绝');
                showLocationPermissionHelp();
                return;
            }
            
            // 继续获取位置
            doGetCurrentPosition();
        }).catch(() => {
            // 权限API不支持，直接尝试获取位置
            logger.info('权限API不支持，直接尝试获取位置');
            doGetCurrentPosition();
        });
    } else {
        logger.info('浏览器不支持权限查询API，直接尝试获取位置');
        doGetCurrentPosition();
    }
}

function doGetCurrentPosition() {
    const options = {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 30000
    };
    
    logger.info(`位置获取选项: 高精度=${options.enableHighAccuracy}, 超时=${options.timeout}ms`);
    logger.info('📍 正在请求地理位置权限...');
    
    navigator.geolocation.getCurrentPosition(
        handleLocationSuccess,
        handleLocationError,
        options
    );
}

async function handleLocationSuccess(position) {
    currentPosition = {
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
        accuracy: position.coords.accuracy,
        altitude: position.coords.altitude,
        altitudeAccuracy: position.coords.altitudeAccuracy,
        heading: position.coords.heading,
        speed: position.coords.speed,
        timestamp: position.timestamp
    };
    
    logger.success(`位置获取成功: ${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`);
    logger.info(`位置精度: ${Math.round(currentPosition.accuracy)}米`);
    
    // 更新坐标显示
    document.getElementById('coordinates').textContent = 
        `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`;
    
    // 更新精度显示
    document.getElementById('accuracy').textContent = `±${Math.round(currentPosition.accuracy)}m`;
    
    // 更新位置显示
    try {
        logger.info('正在获取地址信息...');
        const locationName = await getLocationName(currentPosition.latitude, currentPosition.longitude);
        document.getElementById('currentLocation').textContent = locationName;
        logger.success(`地址获取成功: ${locationName}`);
    } catch (error) {
        logger.warning(`地址获取失败: ${error.message}`);
        document.getElementById('currentLocation').textContent = 
            `${currentPosition.latitude.toFixed(4)}, ${currentPosition.longitude.toFixed(4)}`;
    }
    
    // 记录额外的位置信息
    if (currentPosition.altitude !== null) {
        logger.info(`海拔高度: ${Math.round(currentPosition.altitude)}米`);
    }
    if (currentPosition.speed !== null) {
        logger.info(`移动速度: ${Math.round(currentPosition.speed * 3.6)}km/h`);
    }
    
    // 启用探索按钮
    document.getElementById('exploreBtn').disabled = false;
    logger.success('位置信息更新完成，探索功能已启用');
}

function handleLocationError(error) {
    let errorMessage = '无法获取位置信息';
    let errorDetails = '';
    let showManualInput = false;
    
    switch(error.code) {
        case error.PERMISSION_DENIED:
            errorMessage = '❌ 地理位置权限被拒绝';
            errorDetails = '请重新授权或使用手动输入位置';
            showManualInput = true;
            logger.error('用户拒绝了地理位置权限请求');
            break;
        case error.POSITION_UNAVAILABLE:
            errorMessage = '❌ 位置信息不可用';
            errorDetails = '设备无法确定位置，请检查GPS或网络连接';
            showManualInput = true;
            break;
        case error.TIMEOUT:
            errorMessage = '⏰ 获取位置超时';
            errorDetails = '位置获取时间过长，请重试或手动输入';
            showManualInput = true;
            break;
        default:
            errorMessage = '❓ 未知的位置获取错误';
            errorDetails = `错误代码: ${error.code}`;
            showManualInput = true;
    }
    
    logger.error(`${errorMessage}: ${errorDetails}`);
    logger.error(`错误详情: ${error.message}`);
    
    // 更新UI显示
    document.getElementById('currentLocation').textContent = '获取失败';
    document.getElementById('coordinates').textContent = '无法获取';
    document.getElementById('accuracy').textContent = '无法获取';
    
    // 显示错误信息
    showError(`${errorMessage}\n${errorDetails}`);
    
    // 根据错误类型显示相应的帮助信息
    if (error.code === error.PERMISSION_DENIED) {
        showLocationPermissionHelp();
    }
    
    if (showManualInput) {
        setTimeout(() => {
            showManualLocationInput();
        }, 2000); // 2秒后显示手动输入选项
    }
}

async function getLocationName(lat, lng) {
    // 使用反向地理编码获取地点名称
    // 这里使用一个简单的实现，实际项目中可以使用更好的地理编码服务
    try {
        const response = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${lat}&longitude=${lng}&localityLanguage=zh`);
        const data = await response.json();
        
        if (data.city && data.countryName) {
            return `${data.city}, ${data.countryName}`;
        } else if (data.locality && data.countryName) {
            return `${data.locality}, ${data.countryName}`;
        } else {
            return data.countryName || '未知位置';
        }
    } catch (error) {
        console.error('获取地点名称失败:', error);
        throw error;
    }
}

async function startExploration() {
    logger.info('开始方向探索...');
    
    if (!currentPosition) {
        const errorMsg = '请先获取当前位置';
        logger.error(errorMsg);
        showError(errorMsg);
        return;
    }
    
    if (currentHeading === null || currentHeading === undefined) {
        const errorMsg = '未检测到方向信息，请移动设备或手动输入方向';
        logger.error(errorMsg);
        showError(errorMsg);
        // 尝试启用手动输入
        enableManualHeadingInput();
        return;
    }
    
    // 记录探索参数
    const exploreParams = {
        latitude: currentPosition.latitude,
        longitude: currentPosition.longitude,
        heading: currentHeading,
        segment_distance: settings.segmentDistance,
        time_mode: settings.timeMode,
        speed: settings.speed
    };
    
    logger.info(`探索参数: 位置(${exploreParams.latitude.toFixed(4)}, ${exploreParams.longitude.toFixed(4)})`);
    logger.info(`方向: ${exploreParams.heading}° (${getDirectionText(exploreParams.heading)})`);
    logger.info(`分段距离: ${exploreParams.segment_distance}km, 时间模式: ${exploreParams.time_mode}, 速度: ${exploreParams.speed}km/h`);
    
    // 显示加载状态
    showLoading(true);
    document.getElementById('exploreBtn').disabled = true;
    
    try {
        logger.info('正在向后端发送探索请求...');
        const startTime = Date.now();
        
                // 使用Supabase数据库API端点
        const apiEndpoint = `${API_BASE_URL}/api/explore-supabase`;
        logger.info('使用Supabase数据库数据源');
        
        // 调用后端API计算路径
        const response = await fetch(apiEndpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(exploreParams)
        });
        
        const requestTime = Date.now() - startTime;
        logger.info(`API请求耗时: ${requestTime}ms`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        logger.success(`探索完成! 找到 ${data.places.length} 个地点`);
        logger.info(`总距离: ${data.total_distance}km, 计算时间: ${(data.calculation_time * 1000).toFixed(1)}ms`);
        
        // 保存场景数据并进入选择模式
        sceneManagement.allScenes = data.places;
        sceneManagement.selectedScenes = [];
        sceneManagement.rejectedScenes = [];
        
        displayPlaces(data.places);
        
        // 🎒 自动创建旅程（如果还没有活跃旅程）
        if (!journeyManagement.isJourneyActive && currentPosition) {
            try {
                const locationName = `位置 ${currentPosition.latitude.toFixed(4)}, ${currentPosition.longitude.toFixed(4)}`;
                await startJourney(
                    currentPosition.latitude, 
                    currentPosition.longitude, 
                    locationName,
                    `探索之旅 ${new Date().toLocaleString()}`
                );
                
                // 显示结束旅程按钮
                showEndJourneyButton();
            } catch (error) {
                logger.warning('自动创建旅程失败，将继续不记录旅程');
            }
        }
        
        // 自动进入选择模式
        enableSelectionMode();
        
        // 🆕 强制显示结束旅程按钮（无论旅程是否成功创建）
        showEndJourneyButton();
        
    } catch (error) {
        logger.error(`探索请求失败: ${error.message}`);
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            showError('无法连接到服务器，请确保后端服务正在运行');
        } else {
            showError(`探索请求失败: ${error.message}`);
        }
    } finally {
        showLoading(false);
        document.getElementById('exploreBtn').disabled = false;
        logger.info('探索操作结束');
    }
}

function displayPlaces(places) {
    const container = document.getElementById('placesContainer');
    
    if (!container) {
        logger.error('❌ 找不到地点容器元素 (placesContainer)');
        showError('页面结构错误：缺少地点显示容器');
        return;
    }
    
    container.innerHTML = '';
    
    if (!places || places.length === 0) {
        container.innerHTML = '<div class="error-message">没有找到相关地点信息</div>';
        return;
    }
    
    places.forEach((place, index) => {
        const placeCard = createPlaceCard(place, index);
        if (placeCard && container) {
            container.appendChild(placeCard);
        } else {
            logger.error(`❌ 无法添加地点卡片 ${index}: container=${!!container}, placeCard=${!!placeCard}`);
        }
    });
}

function createPlaceCard(place, index) {
    const card = document.createElement('div');
    
    // 检查场景的选择状态
    const isSelected = sceneManagement.selectedScenes.some(s => s.index === index);
    const isRejected = sceneManagement.rejectedScenes.some(s => s.index === index);
    
    // 🆕 检查是否为当前位置
    const isCurrentLocation = place.isCurrentLocation || false;
    
    card.className = `place-card ${isSelected ? 'selected' : ''} ${isRejected ? 'rejected' : ''} ${isCurrentLocation ? 'current-location' : ''}`;
    card.dataset.placeIndex = index;
    
    const modeText = {
        'present': t('modernMode'),
        'past': t('ancientMode'),
        'future': t('futureMode')
    }[settings.timeMode] || t('modernMode');
    
    // 格式化价格显示
    const formatPrice = (price) => {
        if (!price) return t('noInfo');
        if (price.includes('免费') || price.includes('free')) {
            return `<span class="free-price">${price}</span>`;
        }
        return `<span class="price-highlight">${price}</span>`;
    };
    
    card.innerHTML = `
        ${sceneManagement.isSelectionMode ? `
        <div class="scene-selector">
            <input type="radio" name="scene-selection" class="scene-radio" id="scene-${index}" 
                   ${isSelected ? 'checked' : ''} ${isRejected ? 'disabled' : ''}
                   onchange="toggleSceneSelection(${index})">
            <label for="scene-${index}" class="scene-radio-label" title="选择这个目的地">
                <span class="radio-indicator ${isSelected ? 'selected' : ''}">
                    ${isSelected ? '🎯' : '⭕'}
                </span>
            </label>
            <button class="reject-btn ${isRejected ? 'active' : ''}" 
                    onclick="toggleSceneRejection(${index})"
                    title="${isRejected ? '恢复场景' : '划掉场景'}">
                <span class="icon">${isRejected ? '↻' : '✕'}</span>
            </button>
        </div>
        ` : ''}
        <div class="place-media">
            <img src="${place.image || generatePlaceholderImage(place.name || '暂无图片')}" 
                 alt="${place.name}" 
                 class="place-image"
                 onerror="handleImageError(this, '${place.name || '暂无图片'}')"
                 onclick="showImageModal('${place.image}', '${place.name}')">
            ${place.video ? `
                <div class="video-overlay" onclick="playVideo('${place.video}', '${place.name}')">
                    <div class="play-button">
                        <svg width="60" height="60" viewBox="0 0 24 24" fill="white">
                            <path d="M8 5v14l11-7z"/>
                        </svg>
                    </div>
                    <div class="video-label">📹 观看视频</div>
                </div>
            ` : ''}
        </div>
        <div class="place-content">
            <div class="place-header">
                <h3 class="place-name">
                    ${isCurrentLocation ? '📍 ' : ''}${place.name}
                    ${isCurrentLocation ? `<span class="current-badge">${t('currentLocation')}</span>` : ''}
                </h3>
                <span class="place-distance">${isCurrentLocation ? `0m (${t('currentLocation')})` : formatDistance(place.distance)}</span>
            </div>
            
            ${place.category ? `<div class="place-category">🏷️ ${place.category}</div>` : ''}
            
            <div class="place-location-info">
                📍 ${place.latitude.toFixed(4)}°, ${place.longitude.toFixed(4)}°
                ${place.country ? `| ${place.country}` : ''}
                ${place.city ? ` - ${place.city}` : ''}
            </div>
            
            <p class="place-description">${place.description}</p>
            
            <div class="place-details">
                <div class="detail-item">
                    <div class="detail-label">🕒 开放时间</div>
                    <div class="detail-value">${place.opening_hours || '暂无信息'}</div>
                </div>
                
                <div class="detail-item">
                    <div class="detail-label">💰 门票价格</div>
                    <div class="detail-value">${formatPrice(place.ticket_price)}</div>
                </div>
                
                <div class="detail-item">
                    <div class="detail-label">🎫 购票方式</div>
                    <div class="detail-value">${place.booking_method || '暂无信息'}</div>
                </div>
                
                <div class="detail-item">
                    <div class="detail-label">📍 精确坐标</div>
                    <div class="detail-value">${place.latitude.toFixed(6)}, ${place.longitude.toFixed(6)}</div>
                </div>
            </div>
            
            <div class="place-actions">
                ${isCurrentLocation ? `
                    <button class="action-btn current-location-btn" disabled title="当前位置">
                        📍 当前位置
                    </button>
                    <button class="action-btn selfie-btn" onclick="requireLogin(openSelfieGenerator, ${index}, '${place.name.replace(/'/g, "\\'")}', '${place.city ? place.city.replace(/'/g, "\\'") : (place.country ? place.country.replace(/'/g, "\\'") : "")}')" title="生成景点合影">
                        📸 ${t('generatePhoto')}
                    </button>
                    <button class="action-btn doro-btn" onclick="requireLogin(openDoroSelfie, ${index}, '${place.name.replace(/'/g, "\\'")}', '${place.category ? place.category.replace(/'/g, "\\'") : ""}', '${place.city ? place.city.replace(/'/g, "\\'") : (place.country ? place.country.replace(/'/g, "\\'") : "")}')" title="Doro与我合影">
                        🤝 ${t('doroPhoto')}
                    </button>
                    ${place.latitude && place.longitude ? `
                    <button class="action-btn streetview-btn" onclick="requireLogin(openStreetView, ${place.latitude}, ${place.longitude}, '${place.name.replace(/'/g, "\\'")}')" title="查看街景">
                        🏙️ 查看街景
                    </button>
                    ` : ''}
                ` : `
                    <button class="action-btn selfie-btn" onclick="requireLogin(openSelfieGenerator, ${index}, '${place.name.replace(/'/g, "\\'")}', '${place.city ? place.city.replace(/'/g, "\\'") : (place.country ? place.country.replace(/'/g, "\\'") : "")}')" title="生成景点合影">
                        📸 ${t('generatePhoto')}
                    </button>
                    <button class="action-btn doro-btn" onclick="requireLogin(openDoroSelfie, ${index}, '${place.name.replace(/'/g, "\\'")}', '${place.category ? place.category.replace(/'/g, "\\'") : ""}', '${place.city ? place.city.replace(/'/g, "\\'") : (place.country ? place.country.replace(/'/g, "\\'") : "")}')" title="Doro与我合影">
                        🤝 ${t('doroPhoto')}
                    </button>
                    ${place.latitude && place.longitude ? `
                    <button class="action-btn streetview-btn" onclick="requireLogin(openStreetView, ${place.latitude}, ${place.longitude}, '${place.name.replace(/'/g, "\\'")}')" title="查看街景">
                        🏙️ 查看街景
                    </button>
                    ` : ''}
                `}
            </div>
            
            <span class="place-mode">${modeText}模式</span>
        </div>
    `;
    
    return card;
}

function toggleSettings() {
    const panel = document.getElementById('settingsPanel');
    panel.classList.toggle('show');
}

function updateSettings() {
    settings.segmentDistance = parseInt(document.getElementById('segmentDistance').value);
    settings.timeMode = document.getElementById('timeMode').value;
    settings.speed = parseInt(document.getElementById('speed').value);
    
    logger.info(`设置已更新: ${settings.segmentDistance}km, ${settings.timeMode}模式, ${settings.speed}km/h`);
}

function showLoading(show) {
    const loading = document.getElementById('loading');
    loading.style.display = show ? 'block' : 'none';
}

function showError(message) {
    // 移除现有的错误消息
    const existingError = document.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // 创建新的错误消息
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    // 插入到状态区域后面
    const statusSection = document.querySelector('.status-section');
    statusSection.insertAdjacentElement('afterend', errorDiv);
    
    // 5秒后自动移除
    setTimeout(() => {
        if (errorDiv.parentNode) {
            errorDiv.remove();
        }
    }, 5000);
}

function showSuccess(message) {
    // 移除现有的成功消息
    const existingSuccess = document.querySelector('.success-message');
    if (existingSuccess) {
        existingSuccess.remove();
    }
    
    // 创建新的成功消息
    const successDiv = document.createElement('div');
    successDiv.className = 'success-message';
    successDiv.textContent = message;
    
    // 插入到状态区域后面
    const statusSection = document.querySelector('.status-section');
    statusSection.insertAdjacentElement('afterend', successDiv);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (successDiv.parentNode) {
            successDiv.remove();
        }
    }, 3000);
}

// 清空日志函数
function clearLogs() {
    logger.clear();
    logger.info('日志已清空');
}

// 调试功能：模拟方向（用于桌面测试）
function simulateHeading(degrees) {
    currentHeading = degrees;
    updateCompassDisplay(degrees);
    logger.info(`模拟方向设置为: ${degrees}° (${getDirectionText(degrees)})`);
}

// 调试信息函数
function debugInfo() {
    logger.info('=== 调试信息 ===');
    logger.info(`当前位置: ${currentPosition ? `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}` : '未获取'}`);
    logger.info(`位置精度: ${currentPosition ? `±${Math.round(currentPosition.accuracy)}m` : '未知'}`);
    logger.info(`当前方向: ${currentHeading !== null ? `${Math.round(currentHeading)}° (${getDirectionText(currentHeading)})` : '未检测'}`);
    logger.info(`设置: 分段${settings.segmentDistance}km, ${settings.timeMode}模式, ${settings.speed}km/h`);
    logger.info(`浏览器: ${navigator.userAgent}`);
    logger.info(`屏幕: ${screen.width}x${screen.height}`);
    logger.info('===============');
}

// 获取系统状态
function getSystemStatus() {
    const status = {
        hasPosition: !!currentPosition,
        hasHeading: currentHeading !== null && currentHeading !== undefined,
        geolocationSupported: 'geolocation' in navigator,
        orientationSupported: 'DeviceOrientationEvent' in window,
        isSecureContext: window.isSecureContext,
        userAgent: navigator.userAgent
    };
    
    logger.info('系统状态检查:');
    Object.entries(status).forEach(([key, value]) => {
        const type = value ? 'success' : 'warning';
        logger.log(`${key}: ${value}`, type);
    });
    
    return status;
}

// 场景选择管理函数 - 单选模式（背包客模式）
function toggleSceneSelection(index) {
    const place = sceneManagement.allScenes[index];
    if (!place) return;
    
    // 检查是否已被划掉
    if (sceneManagement.rejectedScenes.some(s => s.index === index)) {
        logger.warning(`场景 ${place.name} 已被划掉，无法选择`);
        return;
    }
    
    const currentSelected = sceneManagement.selectedScenes.find(s => s.index === index);
    
    if (currentSelected) {
        // 如果点击的是已选中的场景，取消选择
        sceneManagement.selectedScenes = [];
        logger.info(`取消选择场景: ${place.name}`);
        
        // 隐藏到达确认界面
        const confirmationDiv = document.getElementById('arrivalConfirmation');
        if (confirmationDiv) {
            confirmationDiv.remove();
        }
        // 显示所有场景
        showAllScenes();
    } else {
        // 单选模式：清空之前的选择，选择当前场景
        const previousSelection = sceneManagement.selectedScenes[0];
        if (previousSelection) {
            logger.info(`取消之前的选择: ${previousSelection.place.name}`);
            updateSceneCard(previousSelection.index);
        }
        
        sceneManagement.selectedScenes = [{ index, place }];
        logger.success(`🎯 选择目的地: ${place.name}`);
        
        // 🎯 新功能：直接进入到达确认流程
        logger.info('🚶‍♂️ 准备前往目的地...');
        
        // 🎯 关键修复：立即更新当前位置为选择的场景位置
        if (place.latitude && place.longitude) {
            currentPosition = {
                latitude: parseFloat(place.latitude),
                longitude: parseFloat(place.longitude)
            };
            
            // 更新UI显示的当前位置（异步处理）
            updateLocationDisplayAsync(place);
            
            // 🆕 添加到历史场景显示
            addToHistoryScenes(place);
        }
        
        // 隐藏其他场景，专注当前目标
        hideOtherScenes(index);
        
        // 直接显示"到达确认"界面
        showArrivalConfirmation({ index, place });
    }
    
    // 更新所有场景卡片的显示状态
    sceneManagement.allScenes.forEach((_, i) => {
        updateSceneCard(i);
    });
}

function toggleSceneRejection(index) {
    const place = sceneManagement.allScenes[index];
    if (!place) return;
    
    const rejectedIndex = sceneManagement.rejectedScenes.findIndex(s => s.index === index);
    
    if (rejectedIndex > -1) {
        // 取消划掉
        sceneManagement.rejectedScenes.splice(rejectedIndex, 1);
        logger.info(`恢复场景: ${place.name}`);
    } else {
        // 划掉场景
        sceneManagement.rejectedScenes.push({ index, place });
        // 同时从选中列表中移除
        const selectedIndex = sceneManagement.selectedScenes.findIndex(s => s.index === index);
        if (selectedIndex > -1) {
            sceneManagement.selectedScenes.splice(selectedIndex, 1);
        }
        logger.info(`划掉场景: ${place.name}`);
    }
    
    updateSceneCard(index);
}

function updateSceneCard(index) {
    const card = document.querySelector(`[data-place-index="${index}"]`);
    if (!card) return;
    
    const isSelected = sceneManagement.selectedScenes.some(s => s.index === index);
    const isRejected = sceneManagement.rejectedScenes.some(s => s.index === index);
    
    card.classList.toggle('selected', isSelected);
    card.classList.toggle('rejected', isRejected);
    
    const checkbox = card.querySelector('.scene-checkbox');
    if (checkbox) {
        checkbox.checked = isSelected;
        checkbox.disabled = isRejected;
    }
    
    const rejectBtn = card.querySelector('.reject-btn');
    if (rejectBtn) {
        rejectBtn.classList.toggle('active', isRejected);
        rejectBtn.querySelector('.icon').textContent = isRejected ? '↻' : '✕';
        rejectBtn.title = isRejected ? '恢复场景' : '划掉场景';
    }
}



function enableSelectionMode() {
    sceneManagement.isSelectionMode = true;
    document.body.classList.add('selection-mode');
    
    // 重新渲染所有卡片
    const places = sceneManagement.allScenes;
    displayPlaces(places);
    
    logger.info('进入场景选择模式');
}

function disableSelectionMode() {
    sceneManagement.isSelectionMode = false;
    document.body.classList.remove('selection-mode');
    
    // 重新渲染所有卡片
    const places = sceneManagement.allScenes;
    displayPlaces(places);
    
    logger.info('退出场景选择模式');
}







// 隐藏其他场景，只显示选中的场景
function hideOtherScenes(selectedIndex) {
    const allCards = document.querySelectorAll('.place-card');
    allCards.forEach((card, index) => {
        if (index !== selectedIndex) {
            card.style.display = 'none';
            card.classList.add('hidden-scene');
        } else {
            card.classList.add('focused-scene');
            const selector = card.querySelector('.scene-selector');
            if (selector) {
                selector.style.display = 'none'; // 隐藏选择器
            }
        }
    });
    
    // 隐藏选择控制面板
    const selectionPanel = document.querySelector('.selection-panel');
    if (selectionPanel) {
        selectionPanel.style.display = 'none';
    }
}

// 显示所有场景
function showAllScenes() {
    const allCards = document.querySelectorAll('.place-card');
    allCards.forEach((card) => {
        card.style.display = 'block';
        card.classList.remove('hidden-scene', 'focused-scene');
        const selector = card.querySelector('.scene-selector');
        if (selector && sceneManagement.isSelectionMode) {
            selector.style.display = 'block'; // 显示选择器
        }
    });
    
    // 显示选择控制面板
    const selectionPanel = document.querySelector('.selection-panel');
    if (selectionPanel && sceneManagement.isSelectionMode) {
        selectionPanel.style.display = 'block';
    }
}

// 显示到达确认界面
function showArrivalConfirmation(selectedScene) {
    // 🆕 设置当前正在确认到达的场景，用于处理"返回"按钮
    sceneManagement.currentlyVisitingScene = selectedScene.place;

    // 尝试多个可能的容器
    let resultsContainer = document.getElementById('results') ||
                          document.getElementById('placesContainer') ||
                          document.querySelector('.places-container');

    if (!resultsContainer) {
        logger.error('❌ 找不到结果容器，无法显示到达确认界面');
        return;
    }

    // 移除可能存在的旧确认界面
    const existingConfirmation = document.getElementById('arrivalConfirmation');
    if (existingConfirmation) {
        existingConfirmation.remove();
    }

    logger.info(`🎯 显示到达确认界面: ${selectedScene.place.name}`);
    
    // 在选中的场景卡片下方添加到达确认区域
    const confirmationHtml = `
        <div class="arrival-confirmation" id="arrivalConfirmation" style="
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            text-align: center;
            border: 2px solid #667eea;
        ">
            <div class="arrival-actions">
                <h3 style="color: #667eea; margin-bottom: 15px;">🎯 当前目标：${selectedScene.place.name}</h3>
                <p style="color: #4a5568; margin-bottom: 20px;">你正在前往这个目的地...</p>
                <div class="arrival-buttons" style="display: flex; gap: 15px; justify-content: center;">
                    <button class="btn btn-primary arrival-btn" onclick="confirmArrival(${selectedScene.index})" style="
                        padding: 15px 30px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border: none;
                        border-radius: 12px;
                        font-size: 16px;
                        font-weight: bold;
                        cursor: pointer;
                        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
                        transition: all 0.3s ease;
                    ">
                        📍 我已到达
                    </button>
                    <button class="btn btn-secondary back-btn" onclick="backToSelection()" style="
                        padding: 15px 30px;
                        background: rgba(255, 255, 255, 0.9);
                        color: #4a5568;
                        border: 2px solid #e2e8f0;
                        border-radius: 12px;
                        font-size: 16px;
                        cursor: pointer;
                        transition: all 0.3s ease;
                    ">
                        ↶ 重新选择
                    </button>
                </div>
            </div>
        </div>
    `;
    
    resultsContainer.insertAdjacentHTML('beforeend', confirmationHtml);
    
    // 滚动到确认界面
    setTimeout(() => {
        const confirmationDiv = document.getElementById('arrivalConfirmation');
        if (confirmationDiv) {
            confirmationDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
}

// 确认到达目的地
async function confirmArrival(index) {
    const arrivedScene = sceneManagement.allScenes[index];
    if (!arrivedScene) return;

    logger.success(`🏁 已到达: ${arrivedScene.name}`);

    // 🆕 清空当前访问的场景标记，因为已经正式到达
    sceneManagement.currentlyVisitingScene = null;
    
    // 🎯 关键功能：更新用户当前位置为到达的场景位置
    if (arrivedScene.latitude && arrivedScene.longitude) {
        currentPosition = {
            latitude: parseFloat(arrivedScene.latitude),
            longitude: parseFloat(arrivedScene.longitude)
        };
        
        // 更新UI显示的当前位置
        try {
            const locationName = await getLocationName(currentPosition.latitude, currentPosition.longitude);
            document.getElementById('currentLocation').textContent = locationName;
            document.getElementById('coordinates').textContent = 
                `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`;
            logger.success(`📍 当前位置已更新为: ${arrivedScene.name}`);
        } catch (error) {
            document.getElementById('currentLocation').textContent = arrivedScene.name;
            document.getElementById('coordinates').textContent = 
                `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`;
            logger.success(`📍 当前位置已更新为: ${arrivedScene.name}`);
        }
    }
    
    // 🎒 记录用户访问的场景到旅程中
    if (journeyManagement.isJourneyActive && journeyManagement.currentJourneyId) {
        try {
            await recordSceneVisit(
                journeyManagement.currentJourneyId,
                arrivedScene,
                null, // 暂时不收集用户评分
                `通过OrientDiscover探索发现的场景` // 自动备注
            );
            logger.info('✅ 场景访问记录已保存到旅程中');
            
            // 🆕 添加到历史场景显示
            addToHistoryScenes(arrivedScene);
            
        } catch (error) {
            logger.warning('记录场景访问失败，但不影响继续使用');
            // 即使API失败，也添加到本地历史记录
            addToHistoryScenes(arrivedScene);
        }
    } else {
        logger.warning('当前没有活跃旅程，场景访问未被记录');
        // 没有活跃旅程时也保存历史记录
        addToHistoryScenes(arrivedScene);
    }
    
    // 🤖 生成AI场景锐评
    await generateAndShowSceneReview(arrivedScene);
    
    showSuccess(`🎉 欢迎来到 ${arrivedScene.name}！`);
    
    // 显示继续探索的选项
    showContinueExplorationOptions(arrivedScene);

    // 🆕 显示Google街景（如果可用）
    showStreetViewForLocation(arrivedScene);
}

// 显示继续探索的选项
function showContinueExplorationOptions(currentScene) {
    const confirmationDiv = document.getElementById('arrivalConfirmation');
    if (confirmationDiv) {
        confirmationDiv.innerHTML = `
            <div class="continue-exploration">
                <h3>🎉 已到达：${currentScene.name}</h3>
                <p>你现在在这里，想要继续探索吗？</p>
                <div class="continue-buttons">
                    <button class="btn btn-primary continue-btn" onclick="continueExploration(${currentScene.latitude}, ${currentScene.longitude})">
                        🗺️ 从这里继续探索
                    </button>
                    <button class="btn btn-secondary end-btn" onclick="endJourney()">
                        🏠 结束今天的旅程
                    </button>
                </div>
            </div>
        `;
    }
}

// 从当前位置继续探索
async function continueExploration(lat, lng) {
    logger.info('🧭 准备从新位置继续探索...');
    
    // 🎯 关键修复：更新当前位置（使用正确的属性名）
    currentPosition = {
        latitude: parseFloat(lat),
        longitude: parseFloat(lng),
        accuracy: 100, // 设置默认精度
        altitude: null,
        altitudeAccuracy: null,
        heading: null,
        speed: null,
        timestamp: Date.now()
    };
    
    logger.success(`📍 位置已更新为: ${lat}, ${lng}`);
    
    // 🎯 立即更新UI显示
    document.getElementById('coordinates').textContent = 
        `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`;
    document.getElementById('accuracy').textContent = '±100m (继续探索)';
    
    // 获取并更新地址显示
    try {
        const locationName = await getLocationName(currentPosition.latitude, currentPosition.longitude);
        document.getElementById('currentLocation').textContent = locationName;
        logger.success(`地址获取成功: ${locationName}`);
    } catch (error) {
        document.getElementById('currentLocation').textContent = `新位置 ${lat}, ${lng}`;
        logger.warning('地址获取失败，使用坐标显示');
    }
    
    // 清除之前的结果
    clearResults();
    
    // 重置场景管理状态
    sceneManagement.allScenes = [];
    sceneManagement.selectedScenes = [];
    sceneManagement.rejectedScenes = [];
    sceneManagement.isSelectionMode = false;
    
    showSuccess('📍 位置已更新！请设置新的探索方向并点击"开始探索"');
    
    // 回到探索界面
    document.getElementById('controls').style.display = 'block';
}

// 结束旅程
async function endJourney() {
    logger.info('🏠 准备结束旅程...');
    
    // 🎒 调用后端API结束旅程
    if (journeyManagement.isJourneyActive && journeyManagement.currentJourneyId) {
        try {
            const result = await endCurrentJourney(journeyManagement.currentJourneyId);
            
            // 显示旅程摘要
            await showJourneySummary(result);
            
        } catch (error) {
            logger.warning('结束旅程API调用失败，但将继续本地清理');
        }
    }
    
    logger.success('🏠 旅程结束，感谢使用背包客探索工具！');
    showSuccess('✨ 期待您的下次探索！');
    
    // 隐藏结束旅程按钮
    hideEndJourneyButton();
    
    // TODO: 生成旅程总结卡片
    // TODO: 统计访问场景、总距离等
    
    // 重置所有状态
    clearResults();
    resetToInitialState();
}

// 显示旅程摘要
function showJourneySummary(journeyResult) {
    const summaryHtml = `
        <div class="journey-summary" style="
            margin: 20px 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        ">
            <h3 style="margin: 0 0 16px 0; font-size: 1.6rem;">🎉 旅程完成！</h3>
            <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 16px;">
                <div>
                    <div style="font-size: 2rem; font-weight: bold;">${journeyResult.visited_scenes_count}</div>
                    <div style="font-size: 0.9rem; opacity: 0.8;">访问场景</div>
                </div>
                <div>
                    <div style="font-size: 2rem; font-weight: bold;">${journeyResult.total_distance_km.toFixed(1)}</div>
                    <div style="font-size: 0.9rem; opacity: 0.8;">总距离(km)</div>
                </div>
                <div>
                    <div style="font-size: 2rem; font-weight: bold;">⭐</div>
                    <div style="font-size: 0.9rem; opacity: 0.8;">探索完成</div>
                </div>
            </div>
        </div>
    `;
    
    // 在结果区域显示摘要
    const resultsContainer = document.getElementById('results');
    if (resultsContainer) {
        resultsContainer.insertAdjacentHTML('afterbegin', summaryHtml);
        
        // 3秒后自动隐藏摘要
        setTimeout(() => {
            const summaryDiv = document.querySelector('.journey-summary');
            if (summaryDiv) {
                summaryDiv.style.opacity = '0';
                summaryDiv.style.transition = 'opacity 1s ease';
                setTimeout(() => summaryDiv.remove(), 1000);
            }
        }, 5000);
    }
}

// 返回场景选择
function backToSelection() {
    // 🆕 如果有当前正在访问的场景，从历史记录中移除它
    if (sceneManagement.currentlyVisitingScene) {
        // 从历史场景列表中移除当前场景
        const sceneIndex = journeyManagement.historyScenes.findIndex(
            scene => scene.name === sceneManagement.currentlyVisitingScene.name
        );

        if (sceneIndex !== -1) {
            const removedScene = journeyManagement.historyScenes.splice(sceneIndex, 1)[0];
            logger.info(`🗑️ 已从历史记录中移除场景: ${removedScene.name}`);

            // 重新编号访问顺序
            journeyManagement.historyScenes.forEach((scene, index) => {
                scene.visitOrder = index + 1;
            });

            // 重新显示历史场景
            displayHistoryScenes();
        }

        // 清空当前访问的场景
        sceneManagement.currentlyVisitingScene = null;
    }

    // 恢复所有场景的显示
    const allCards = document.querySelectorAll('.place-card');
    allCards.forEach(card => {
        card.style.display = 'block';
        card.classList.remove('hidden-scene', 'focused-scene');

        // 恢复选择器
        const selector = card.querySelector('.scene-selector');
        if (selector) {
            selector.style.display = 'block';
        }
    });

    // 移除到达确认区域
    const confirmationDiv = document.getElementById('arrivalConfirmation');
    if (confirmationDiv) {
        confirmationDiv.remove();
    }

    // 恢复选择控制面板
    const selectionPanel = document.querySelector('.selection-panel');
    if (selectionPanel) {
        selectionPanel.style.display = 'block';
    }

    // 清空当前选择，让用户重新选择
    sceneManagement.selectedScenes = [];

    // 更新所有卡片状态
    sceneManagement.allScenes.forEach((_, i) => {
        updateSceneCard(i);
    });

    logger.info('↶ 已返回场景选择，已清除历史记录');
}

// 重置到初始状态
function resetToInitialState() {
    // 重置场景管理状态
    sceneManagement.allScenes = [];
    sceneManagement.selectedScenes = [];
    sceneManagement.rejectedScenes = [];
    sceneManagement.isSelectionMode = false;
    sceneManagement.currentlyVisitingScene = null; // 🆕 重置当前访问场景标记
    
    // 🎒 重置旅程管理状态
    journeyManagement.currentJourneyId = null;
    journeyManagement.isJourneyActive = false;
    journeyManagement.startLocation = null;
    journeyManagement.visitedScenes = [];
    journeyManagement.totalDistance = 0;
    
    // 清除历史场景显示
    journeyManagement.historyScenes = [];
    const historySection = document.getElementById('journeyHistorySection');
    if (historySection) {
        historySection.style.display = 'none';
    }
    
    // 清除结果显示
    clearResults();
    
    // 显示控制面板
    const controls = document.getElementById('controls');
    if (controls) {
        controls.style.display = 'block';
    }
    
    logger.info('🔄 已重置到初始状态');
}



// ========== 旅程管理功能 ==========

/**
 * 开始新的旅程
 * @param {number} lat - 起始纬度
 * @param {number} lng - 起始经度
 * @param {string} locationName - 起始位置名称
 * @param {string} journeyTitle - 旅程标题（可选）
 */
async function startJourney(lat, lng, locationName, journeyTitle = null) {
    try {
        logger.info('🎒 开始创建新旅程...');
        
        const response = await fetch(`${API_BASE_URL}/api/journey/start`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                start_lat: lat,
                start_lng: lng,
                start_name: locationName,
                journey_title: journeyTitle || `探索之旅 ${new Date().toLocaleString()}`
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // 更新旅程状态
            journeyManagement.currentJourneyId = data.journey_id;
            journeyManagement.isJourneyActive = true;
            journeyManagement.startLocation = {
                lat: lat,
                lng: lng,
                name: locationName
            };
            journeyManagement.visitedScenes = [];
            
            logger.success(data.message);
            logger.info(`旅程ID: ${data.journey_id}`);
            
            return data.journey_id;
        } else {
            throw new Error('创建旅程失败');
        }
        
    } catch (error) {
        logger.error(`创建旅程失败: ${error.message}`);
        showError('创建旅程失败，请重试');
        throw error;
    }
}

/**
 * 记录访问场景
 * @param {string} journeyId - 旅程ID
 * @param {object} scene - 场景对象
 * @param {number} rating - 用户评分（可选）
 * @param {string} notes - 用户备注（可选）
 */
async function recordSceneVisit(journeyId, scene, rating = null, notes = null) {
    try {
        logger.info(`📍 记录场景访问: ${scene.name}`);
        
        const response = await fetch(`${API_BASE_URL}/api/journey/visit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                journey_id: journeyId,
                scene_name: scene.name,
                scene_lat: scene.latitude,
                scene_lng: scene.longitude,
                scene_address: scene.address || scene.description,
                user_rating: rating,
                notes: notes
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // 更新本地状态
            journeyManagement.visitedScenes.push({
                name: scene.name,
                location: { lat: scene.latitude, lng: scene.longitude },
                visitTime: new Date().toISOString()
            });
            
            logger.success(data.message);
            logger.info(`已访问场景数: ${data.visited_scenes_count}`);
            
            return data;
        } else {
            throw new Error('记录访问失败');
        }
        
    } catch (error) {
        logger.error(`记录场景访问失败: ${error.message}`);
        showError('记录访问失败，请重试');
        throw error;
    }
}

/**
 * 结束当前旅程
 * @param {string} journeyId - 旅程ID
 */
async function endCurrentJourney(journeyId) {
    try {
        logger.info('🏠 结束当前旅程...');
        
        const response = await fetch(`${API_BASE_URL}/api/journey/${journeyId}/end`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            // 重置旅程状态
            journeyManagement.currentJourneyId = null;
            journeyManagement.isJourneyActive = false;
            journeyManagement.visitedScenes = [];
            
            logger.success(data.message);
            logger.info(`总访问场景: ${data.visited_scenes_count}`);
            
            return data;
        } else {
            throw new Error('结束旅程失败');
        }
        
    } catch (error) {
        logger.error(`结束旅程失败: ${error.message}`);
        showError('结束旅程失败，请重试');
        throw error;
    }
}

/**
 * 获取当前旅程信息
 * @param {string} journeyId - 旅程ID
 */
async function getCurrentJourneyInfo(journeyId) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/journey/${journeyId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            return data.journey;
        } else {
            throw new Error('获取旅程信息失败');
        }
        
    } catch (error) {
        logger.error(`获取旅程信息失败: ${error.message}`);
        return null;
    }
}

// 在控制台中暴露调试函数
window.simulateHeading = simulateHeading;
window.debugInfo = debugInfo;
window.clearLogs = clearLogs;
window.getSystemStatus = getSystemStatus;
window.logger = logger;
// 显示结束旅程按钮
function showEndJourneyButton() {
    const endJourneyBtn = document.getElementById('endJourneyBtn');
    if (endJourneyBtn) {
        endJourneyBtn.style.display = 'block';
        logger.info('🏠 结束旅程按钮已显示');
        
        // 如果旅程没有激活，也要显示按钮（用户可能想手动管理旅程）
        if (!journeyManagement.isJourneyActive) {
            logger.warning('⚠️ 旅程未激活但显示结束按钮，建议检查旅程创建逻辑');
        }
    }
}

// 隐藏结束旅程按钮
function hideEndJourneyButton() {
    const endJourneyBtn = document.getElementById('endJourneyBtn');
    if (endJourneyBtn) {
        endJourneyBtn.style.display = 'none';
    }
}

// 添加场景到历史记录
function addToHistoryScenes(scene, reviewData = null) {
    // 避免重复添加
    const exists = journeyManagement.historyScenes.find(h => h.name === scene.name);
    if (!exists) {
        const historyScene = {
            ...scene,
            visitTime: new Date().toLocaleString(),
            visitOrder: journeyManagement.historyScenes.length + 1,
            reviewData: reviewData // 保存锐评数据
        };
        journeyManagement.historyScenes.push(historyScene);
        displayHistoryScenes();
        logger.info(`📚 场景 "${scene.name}" 已添加到历史记录`);
    } else if (reviewData && !exists.reviewData) {
        // 如果场景已存在但没有锐评数据，则添加锐评数据
        exists.reviewData = reviewData;
        displayHistoryScenes();
        logger.info(`📝 为场景 "${scene.name}" 添加了锐评数据`);
    }
}

// 显示历史访问场景
function displayHistoryScenes() {
    const historySection = document.getElementById('journeyHistorySection');
    const historyContainer = document.getElementById('historyPlacesContainer');
    
    if (!historySection || !historyContainer) return;
    
    if (journeyManagement.historyScenes.length === 0) {
        historySection.style.display = 'none';
        return;
    }
    
    historySection.style.display = 'block';
    historyContainer.innerHTML = '';
    
    journeyManagement.historyScenes.forEach((scene, index) => {
        const historyCard = document.createElement('div');
        historyCard.className = `history-place-card ${scene.reviewData ? 'has-review' : 'no-review'}`;
        historyCard.style.cursor = scene.reviewData ? 'pointer' : 'default';
        
        historyCard.innerHTML = `
            <img src="${scene.image || 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuaaguaXoOWbvueJhzwvdGV4dD48L3N2Zz4='}" 
                 alt="${scene.name}" 
                 class="place-image"
                 onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxOCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuaaguaXoOWbvueJhzwvdGV4dD48L3N2Zz4='"
            <div class="place-content">
                <div class="place-header">
                    <h3 class="place-name">${scene.name}</h3>
                    <span class="visit-order">#${scene.visitOrder}</span>
                </div>
                <p class="place-description">${scene.description}</p>
                <div class="place-meta">
                    <span class="visit-time">🕒 ${scene.visitTime}</span>
                    <span class="place-coordinates">📍 ${scene.latitude.toFixed(4)}, ${scene.longitude.toFixed(4)}</span>
                </div>
                ${scene.reviewData ? `
                    <div class="review-indicator" style="
                        position: absolute;
                        top: 10px;
                        left: 10px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 5px 10px;
                        border-radius: 15px;
                        font-size: 0.8rem;
                        font-weight: 600;
                        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
                        z-index: 5;
                    ">
                        🤖 有锐评
                    </div>
                ` : ''}
            </div>
        `;
        
        // 添加点击事件
        if (scene.reviewData) {
            historyCard.addEventListener('click', () => {
                showSceneReviewModal(scene.reviewData, scene);
            });
            historyCard.title = '点击查看AI锐评';
        }
        
        if (historyContainer && historyCard) {
            historyContainer.appendChild(historyCard);
        } else {
            logger.error(`❌ 无法添加历史卡片: historyContainer=${!!historyContainer}, historyCard=${!!historyCard}`);
        }
    });
}

// 显示场景锐评弹窗（独立弹窗，可重复查看）
function showSceneReviewModal(reviewData, scene) {
    // 移除已存在的弹窗
    const existingModal = document.getElementById('reviewModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    const modalHtml = `
        <div class="review-modal" id="reviewModal" style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        ">
            <div class="review-modal-content" style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 20px;
                max-width: 90%;
                max-height: 90%;
                overflow-y: auto;
                box-shadow: 0 12px 48px rgba(0, 0, 0, 0.3);
                position: relative;
                animation: slideUp 0.3s ease;
            ">
                <button class="close-modal-btn" onclick="closeReviewModal()" style="
                    position: absolute;
                    top: 15px;
                    right: 15px;
                    background: rgba(255, 255, 255, 0.2);
                    border: none;
                    color: white;
                    font-size: 24px;
                    width: 40px;
                    height: 40px;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: all 0.3s ease;
                ">✕</button>
                
                <div class="review-header" style="text-align: center; margin-bottom: 25px;">
                    <h2 style="margin: 0 0 10px 0; font-size: 1.8rem;">🤖 ${reviewData.title}</h2>
                    <div style="opacity: 0.9; font-size: 1rem;">AI智能锐评 - ${scene.name}</div>
                    <div style="opacity: 0.8; font-size: 0.9rem; margin-top: 5px;">访问时间: ${scene.visitTime}</div>
                </div>
                
                <div class="review-content" style="margin-bottom: 25px;">
                    <p style="line-height: 1.8; font-size: 1.1rem; margin: 0;">
                        ${reviewData.review}
                    </p>
                </div>
                
                ${reviewData.highlights && reviewData.highlights.length > 0 ? `
                    <div class="review-highlights" style="margin-bottom: 20px;">
                        <h4 style="margin: 0 0 15px 0; font-size: 1.2rem;">✨ 亮点推荐</h4>
                        <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                            ${reviewData.highlights.map(highlight => 
                                `<span style="background: rgba(255, 255, 255, 0.2); padding: 8px 15px; border-radius: 25px; font-size: 0.9rem; font-weight: 500;">
                                    ${highlight}
                                </span>`
                            ).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <div class="review-footer" style="
                    display: grid; 
                    grid-template-columns: 1fr 1fr; 
                    gap: 20px; 
                    background: rgba(255, 255, 255, 0.1); 
                    padding: 20px; 
                    border-radius: 15px;
                ">
                    ${reviewData.tips ? `
                        <div>
                            <div style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">💡 小贴士</div>
                            <div style="font-size: 1rem; opacity: 0.9; line-height: 1.5;">${reviewData.tips}</div>
                        </div>
                    ` : ''}
                    
                    <div>
                        <div style="font-weight: bold; margin-bottom: 8px; font-size: 1.1rem;">🎯 推荐理由</div>
                        <div style="font-size: 1rem; opacity: 0.9; line-height: 1.5;">${reviewData.rating_reason}</div>
                    </div>
                </div>
                
                ${reviewData.mood ? `
                    <div style="text-align: center; margin-top: 20px; font-size: 1rem; opacity: 0.9;">
                        适合心情：${reviewData.mood} 🎭
                    </div>
                ` : ''}
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 添加样式
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        @keyframes slideUp {
            from { 
                opacity: 0;
                transform: translateY(50px);
            }
            to { 
                opacity: 1;
                transform: translateY(0);
            }
        }
        .close-modal-btn:hover {
            background: rgba(255, 255, 255, 0.3) !important;
            transform: scale(1.1);
        }
    `;
    document.head.appendChild(style);
    
    logger.info(`📖 显示场景锐评弹窗: ${scene.name}`);
}

// 关闭锐评弹窗
function closeReviewModal() {
    const modal = document.getElementById('reviewModal');
    if (modal) {
        modal.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => modal.remove(), 300);
        logger.info('📖 锐评弹窗已关闭');
    }
}

// 全局暴露关闭函数
window.closeReviewModal = closeReviewModal;

// 计算两个坐标之间的距离（使用Haversine公式）
function calculateDistance(lat1, lng1, lat2, lng2) {
    const R = 6371; // 地球半径（公里）
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLng = (lng2 - lng1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLng/2) * Math.sin(dLng/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    const distance = R * c;
    return distance;
}

// 格式化距离显示
function formatDistance(distanceKm) {
    if (typeof distanceKm !== 'number') {
        return '0m';
    }
    
    if (distanceKm < 1) {
        // 小于1公里，显示米
        const meters = Math.round(distanceKm * 1000);
        return `${meters}m`;
    } else {
        // 大于等于1公里，显示公里，保留2位小数
        return `${distanceKm.toFixed(2)}km`;
    }
}

// 计算旅程统计数据
function calculateJourneyStats() {
    const scenes = journeyManagement.historyScenes;
    
    if (scenes.length === 0) {
        return {
            totalDistance: 0,
            totalTimeMinutes: 0,
            scenesCount: 0
        };
    }
    
    // 计算总距离
    let totalDistance = 0;
    for (let i = 1; i < scenes.length; i++) {
        const prevScene = scenes[i - 1];
        const currentScene = scenes[i];
        const distance = calculateDistance(
            prevScene.latitude, prevScene.longitude,
            currentScene.latitude, currentScene.longitude
        );
        totalDistance += distance;
    }
    
    // 计算总时长（基于访问时间）
    let totalTimeMinutes = 0;
    if (scenes.length >= 2) {
        const startTime = new Date(scenes[0].visitTime);
        const endTime = new Date(scenes[scenes.length - 1].visitTime);
        totalTimeMinutes = Math.round((endTime - startTime) / (1000 * 60)); // 转换为分钟
        
        // 确保时间是正数
        if (totalTimeMinutes < 0) {
            totalTimeMinutes = Math.round(scenes.length * 5); // 默认每个场景5分钟
        }
    }
    
    return {
        totalDistance: Math.round(totalDistance * 10) / 10, // 保留1位小数
        totalTimeMinutes: Math.max(totalTimeMinutes, scenes.length * 2), // 最少每个场景2分钟
        scenesCount: scenes.length
    };
}

// 增强的旅程总结功能
async function showJourneySummary(journeyResult) {
    // 🔧 使用本地计算的统计数据，而不是依赖后端返回的数据
    const stats = calculateJourneyStats();
    
    // 生成旅程亮点
    const highlights = generateJourneyHighlights();
    
    // 🤖 生成AI旅程总结文字
    let aiSummaryText = '';
    try {
        logger.info('🤖 开始生成AI旅程总结...');
        const aiSummary = await generateAIJourneySummary(stats);
        aiSummaryText = aiSummary || '🎉 恭喜完成这次精彩的探索之旅！每一步都是独特的发现，感谢您选择方向探索派对！';
    } catch (error) {
        logger.warning('AI旅程总结生成失败，使用默认文字');
        aiSummaryText = '🎉 恭喜完成这次精彩的探索之旅！每一步都是独特的发现，感谢您选择方向探索派对！';
    }
    
    const summaryHtml = `
        <div class="journey-summary" id="journeySummary" style="
            margin: 20px 0;
            padding: 25px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 20px;
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
            text-align: center;
            position: relative;
            overflow: hidden;
        ">
            <button class="close-summary-btn" onclick="closeSummary()" style="
                position: absolute;
                top: 15px;
                right: 15px;
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                font-size: 24px;
                width: 40px;
                height: 40px;
                border-radius: 50%;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.3s ease;
                z-index: 10;
            " onmouseover="this.style.background='rgba(255, 255, 255, 0.3)'" 
               onmouseout="this.style.background='rgba(255, 255, 255, 0.2)'">✕</button>
            
            <div style="position: relative; z-index: 2;">
                <h2 style="margin: 0 0 20px 0; font-size: 2rem;">🎉 旅程完成！</h2>
                <div style="
                    display: grid; 
                    grid-template-columns: repeat(3, 1fr); 
                    gap: 20px; 
                    margin: 20px 0;
                ">
                    <div style="text-align: center;">
                        <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 5px;">
                            ${stats.scenesCount}
                        </div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">访问场景</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 5px;">
                            ${stats.totalDistance}
                        </div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">总距离(km)</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 2.5rem; font-weight: bold; margin-bottom: 5px;">
                            ${stats.totalTimeMinutes}
                        </div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">旅程时长(分钟)</div>
                    </div>
                </div>
                
                <!-- AI生成的旅程总结文字 -->
                <div class="ai-summary-text" style="
                    background: rgba(255, 255, 255, 0.15);
                    border-radius: 15px;
                    padding: 20px;
                    margin: 25px 0;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                ">
                    <div style="font-size: 0.9rem; opacity: 0.8; margin-bottom: 8px; text-align: center;">
                        🤖 AI旅程回顾
                    </div>
                    <p style="
                        margin: 0;
                        font-size: 1.1rem;
                        line-height: 1.6;
                        font-style: italic;
                        text-align: center;
                    ">${aiSummaryText}</p>
                </div>
                
                ${highlights.length > 0 ? `
                    <div style="margin-top: 20px; padding: 15px; background: rgba(255, 255, 255, 0.1); border-radius: 15px;">
                        <h3 style="margin: 0 0 10px 0;">✨ 旅程亮点</h3>
                        <div style="font-size: 0.9rem; line-height: 1.6;">
                            ${highlights.join('<br>')}
                        </div>
                    </div>
                ` : ''}
                
                <div style="margin-top: 20px; font-size: 1.1rem; opacity: 0.9;">
                    感谢您选择方向探索派对！期待下次旅程 🧭
                </div>
                
                <div style="margin-top: 15px; font-size: 0.85rem; opacity: 0.7;">
                    💡 提示：此总结将保持显示，您可以点击右上角 ✕ 关闭
                </div>
            </div>
        </div>
    `;
    
    const resultsContainer = document.getElementById('results') || document.getElementById('placesContainer');
    if (resultsContainer) {
        resultsContainer.innerHTML = summaryHtml;
        logger.success(`📊 旅程总结已生成: ${stats.scenesCount}个场景, ${stats.totalDistance}km, ${stats.totalTimeMinutes}分钟`);
    }
}

// 关闭旅程总结
function closeSummary() {
    const summary = document.getElementById('journeySummary');
    if (summary) {
        summary.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => summary.remove(), 300);
        logger.info('📊 旅程总结已关闭');
    }
}

// 全局暴露关闭函数
window.closeSummary = closeSummary;

// 生成旅程亮点
function generateJourneyHighlights() {
    const highlights = [];
    const scenes = journeyManagement.historyScenes;
    
    if (scenes.length > 0) {
        highlights.push(`🎯 首站探索：${scenes[0].name}`);
        
        if (scenes.length > 1) {
            highlights.push(`🏁 终点到达：${scenes[scenes.length - 1].name}`);
        }
        
        if (scenes.length >= 3) {
            highlights.push(`🌟 成就解锁：探索达人（访问${scenes.length}个地点）`);
        }
        
        // 计算旅程总时长（基于访问时间）
        if (scenes.length >= 2) {
            const startTime = new Date(scenes[0].visitTime);
            const endTime = new Date(scenes[scenes.length - 1].visitTime);
            const duration = Math.round((endTime - startTime) / (1000 * 60)); // 分钟
            if (duration > 0) {
                highlights.push(`⏱️ 旅程时长：${duration}分钟`);
            }
        }
    }
    
    return highlights;
}

// 显示地理位置权限帮助信息
function showLocationPermissionHelp() {
    const helpHtml = `
        <div class="location-permission-help" style="
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            max-width: 90%;
            text-align: center;
        ">
            <h3 style="color: #e53e3e; margin-bottom: 15px;">🔒 需要位置权限</h3>
            <p style="margin-bottom: 15px; color: #4a5568;">
                OrientDiscover 需要访问您的位置来提供探索服务
            </p>
            <div style="margin-bottom: 20px; text-align: left; font-size: 14px; color: #666;">
                <strong>解决方法：</strong><br>
                1. 点击浏览器地址栏左侧的锁图标<br>
                2. 选择"位置" → "允许"<br>
                3. 刷新页面重新尝试<br>
                <br>
                <strong>或者：</strong><br>
                • 使用下方的手动输入位置功能
            </div>
            <div style="display: flex; gap: 10px; justify-content: center;">
                <button onclick="this.parentElement.parentElement.remove(); refreshLocation();" 
                        style="padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer;">
                    🔄 重新尝试
                </button>
                <button onclick="this.parentElement.parentElement.remove(); showManualLocationInput();" 
                        style="padding: 10px 20px; background: #f093fb; color: white; border: none; border-radius: 8px; cursor: pointer;">
                    ✋ 手动输入
                </button>
                <button onclick="this.parentElement.parentElement.remove();" 
                        style="padding: 10px 20px; background: #cbd5e0; color: #4a5568; border: none; border-radius: 8px; cursor: pointer;">
                    ❌ 关闭
                </button>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', helpHtml);
}

// 显示手动位置输入界面
function showManualLocationInput() {
    const inputHtml = `
        <div class="manual-location-input" style="
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            z-index: 10000;
            max-width: 90%;
            min-width: 350px;
        ">
            <h3 style="color: #667eea; margin-bottom: 15px; text-align: center;">📍 手动输入位置</h3>
            <div style="margin-bottom: 15px;">
                <label style="display: block; margin-bottom: 5px; font-weight: bold;">纬度 (Latitude):</label>
                <input type="number" id="manualLat" value="40.0888" placeholder="例如: 40.0888" step="0.000001" 
                       style="width: 100%; padding: 10px; border: 1px solid #cbd5e0; border-radius: 8px; font-size: 16px;">
            </div>
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 5px; font-weight: bold;">经度 (Longitude):</label>
                <input type="number" id="manualLng" value="116.3964" placeholder="例如: 116.3964" step="0.000001" 
                       style="width: 100%; padding: 10px; border: 1px solid #cbd5e0; border-radius: 8px; font-size: 16px;">
            </div>
            <div style="margin-bottom: 20px; padding: 10px; background: #f7fafc; border-radius: 8px; font-size: 14px; color: #4a5568;">
                <strong>💡 提示：</strong><br>
                • 北京市中心大约：40.0888, 116.3964<br>
                • 可以在地图应用中查看当前位置的坐标<br>
                • 或者使用"获取我的位置"按钮再次尝试
            </div>
            <div style="display: flex; gap: 10px; justify-content: center;">
                <button onclick="setManualLocation();" 
                        style="padding: 12px 24px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold;">
                    ✅ 确认位置
                </button>
                <button onclick="this.parentElement.parentElement.remove(); refreshLocation();" 
                        style="padding: 12px 24px; background: #f093fb; color: white; border: none; border-radius: 8px; cursor: pointer;">
                    🔄 重新获取
                </button>
                <button onclick="this.parentElement.parentElement.remove();" 
                        style="padding: 12px 24px; background: #cbd5e0; color: #4a5568; border: none; border-radius: 8px; cursor: pointer;">
                    ❌ 取消
                </button>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', inputHtml);
}

// 设置手动输入的位置
async function setManualLocation() {
    const latInput = document.getElementById('manualLat');
    const lngInput = document.getElementById('manualLng');
    
    const lat = parseFloat(latInput.value);
    const lng = parseFloat(lngInput.value);
    
    // 验证输入
    if (isNaN(lat) || isNaN(lng)) {
        alert('❌ 请输入有效的经纬度数值');
        return;
    }
    
    if (lat < -90 || lat > 90) {
        alert('❌ 纬度应该在 -90 到 90 之间');
        return;
    }
    
    if (lng < -180 || lng > 180) {
        alert('❌ 经度应该在 -180 到 180 之间');
        return;
    }
    
    // 设置位置
    currentPosition = {
        latitude: lat,
        longitude: lng,
        accuracy: 1000, // 手动输入精度设为1000米
        altitude: null,
        altitudeAccuracy: null,
        heading: null,
        speed: null,
        timestamp: Date.now()
    };
    
    logger.success(`📍 手动设置位置: ${lat.toFixed(6)}, ${lng.toFixed(6)}`);
    
    // 更新UI
    document.getElementById('coordinates').textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    document.getElementById('accuracy').textContent = '±1000m (手动)';
    
    // 获取地址名称
    try {
        const locationName = await getLocationName(lat, lng);
        document.getElementById('currentLocation').textContent = locationName;
        logger.success(`地址获取成功: ${locationName}`);
    } catch (error) {
        document.getElementById('currentLocation').textContent = `手动位置 ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        logger.warning('地址获取失败，使用坐标显示');
    }
    
    // 启用探索按钮
    document.getElementById('exploreBtn').disabled = false;
    logger.success('✅ 手动位置设置完成，探索功能已启用');
    
    // 关闭输入界面
    const inputModal = document.querySelector('.manual-location-input');
    if (inputModal) {
        inputModal.remove();
    }
}

// 异步更新位置显示
async function updateLocationDisplayAsync(place) {
    try {
        const locationName = await getLocationName(currentPosition.latitude, currentPosition.longitude);
        document.getElementById('currentLocation').textContent = locationName;
        document.getElementById('coordinates').textContent = 
            `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`;
        logger.success(`📍 位置已更新为: ${place.name} (${currentPosition.latitude.toFixed(4)}, ${currentPosition.longitude.toFixed(4)})`);
    } catch (error) {
        document.getElementById('currentLocation').textContent = place.name;
        document.getElementById('coordinates').textContent = 
            `${currentPosition.latitude.toFixed(6)}, ${currentPosition.longitude.toFixed(6)}`;
        logger.success(`📍 位置已更新为: ${place.name}`);
    }
}

// 生成并显示场景锐评
async function generateAndShowSceneReview(scene) {
    try {
        logger.info(`🤖 开始为场景 "${scene.name}" 生成AI锐评...`);
        
        // 准备用户上下文
        const userContext = {
            visit_count: journeyManagement.historyScenes.length,
            time_of_day: new Date().toLocaleTimeString(),
            previous_places: journeyManagement.historyScenes.map(h => h.name),
            journey_active: journeyManagement.isJourneyActive
        };
        
        // 调用后端API生成锐评
        const response = await fetch(`${API_BASE_URL}/api/scene-review`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                scene_name: scene.name,
                scene_description: scene.description,
                scene_type: scene.category || "自然景观",
                scene_lat: scene.latitude,
                scene_lng: scene.longitude,
                user_context: userContext
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.success) {
            displaySceneReview(data.review_data, scene);
            // 🆕 将锐评数据保存到历史场景
            addToHistoryScenes(scene, data.review_data);
            logger.success(`🤖 AI锐评生成成功，耗时: ${data.generation_time.toFixed(2)}秒`);
        } else {
            displaySceneReview(data.review_data, scene);
            // 🆕 即使失败也保存锐评数据（可能是降级版本）
            addToHistoryScenes(scene, data.review_data);
            logger.warning(`⚠️ ${data.message}`);
        }
        
    } catch (error) {
        logger.error(`❌ AI锐评生成失败: ${error.message}`);
        
        // 显示备用锐评
        const fallbackReview = {
            title: `探索发现：${scene.name}`,
            review: `恭喜您发现了${scene.name}！这是一个值得记录的精彩时刻。每一次探索都是独特的体验，每一个地方都有其独特的故事等待您去发现。`,
            highlights: ["独特的探索体验", "值得纪念的时刻", "真实的地理发现"],
            tips: "保持好奇心，享受探索的过程",
            rating_reason: "探索的乐趣",
            mood: "发现"
        };
        
        displaySceneReview(fallbackReview, scene);
        // 🆕 备用锐评也要保存到历史
        addToHistoryScenes(scene, fallbackReview);
    }
}

// 显示场景锐评
function displaySceneReview(reviewData, scene) {
    const confirmationDiv = document.getElementById('arrivalConfirmation');
    if (!confirmationDiv) return;
    
    const reviewHtml = `
        <div class="scene-review" style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 15px;
            margin: 20px 0;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        ">
            <div class="review-header" style="text-align: center; margin-bottom: 20px;">
                <h3 style="margin: 0 0 10px 0; font-size: 1.5rem;">🤖 ${reviewData.title}</h3>
                <div style="opacity: 0.9; font-size: 0.9rem;">AI智能锐评</div>
            </div>
            
            <div class="review-content" style="margin-bottom: 20px;">
                <p style="line-height: 1.6; font-size: 1rem; margin: 0;">
                    ${reviewData.review}
                </p>
            </div>
            
            ${reviewData.highlights && reviewData.highlights.length > 0 ? `
                <div class="review-highlights" style="margin-bottom: 15px;">
                    <h4 style="margin: 0 0 10px 0; font-size: 1.1rem;">✨ 亮点推荐</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 8px;">
                        ${reviewData.highlights.map(highlight => 
                            `<span style="background: rgba(255, 255, 255, 0.2); padding: 5px 12px; border-radius: 20px; font-size: 0.85rem;">
                                ${highlight}
                            </span>`
                        ).join('')}
                    </div>
                </div>
            ` : ''}
            
            <div class="review-footer" style="
                display: grid; 
                grid-template-columns: 1fr 1fr; 
                gap: 15px; 
                background: rgba(255, 255, 255, 0.1); 
                padding: 15px; 
                border-radius: 10px;
            ">
                ${reviewData.tips ? `
                    <div>
                        <div style="font-weight: bold; margin-bottom: 5px;">💡 小贴士</div>
                        <div style="font-size: 0.9rem; opacity: 0.9;">${reviewData.tips}</div>
                    </div>
                ` : ''}
                
                <div>
                    <div style="font-weight: bold; margin-bottom: 5px;">🎯 推荐理由</div>
                    <div style="font-size: 0.9rem; opacity: 0.9;">${reviewData.rating_reason}</div>
                </div>
            </div>
            
            ${reviewData.mood ? `
                <div style="text-align: center; margin-top: 15px; font-size: 0.9rem; opacity: 0.8;">
                    适合心情：${reviewData.mood} 🎭
                </div>
            ` : ''}
        </div>
    `;
    
    // 在到达确认界面前插入锐评
    confirmationDiv.insertAdjacentHTML('beforebegin', reviewHtml);
    
    // 滚动到锐评位置
    setTimeout(() => {
        const reviewDiv = document.querySelector('.scene-review');
        if (reviewDiv) {
            reviewDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
    
    logger.info('🎨 场景锐评已显示');
}

// 生成AI旅程总结
async function generateAIJourneySummary(stats) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/journey-summary`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                visited_scenes: journeyManagement.historyScenes,
                total_distance: stats.totalDistance,
                journey_duration: `${stats.totalTimeMinutes}分钟`,
                scenes_count: stats.scenesCount
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        
        if (data.success && data.summary) {
            logger.success('🤖 AI旅程总结生成成功');
            return data.summary;
        } else {
            throw new Error(data.message || '生成失败');
        }
        
    } catch (error) {
        logger.error(`❌ AI旅程总结生成失败: ${error.message}`);
        return null;
    }
}

// ================ Google街景功能 ================

// 初始化Google Maps API
function initGoogleMapsAPI() {
    if (typeof google !== 'undefined' && google.maps) {
        // 初始化Street View服务
        streetViewService = new google.maps.StreetViewService();
        logger.info('✅ Google Maps Street View服务已初始化');
        return true;
    } else {
        logger.warning('⚠️ Google Maps API未加载');
        return false;
    }
}

// 显示指定位置的Google街景
async function showStreetViewForLocation(scene) {
    // 等待Google Maps API加载
    const maxWaitTime = 10000; // 最多等待10秒
    const checkInterval = 500; // 每500ms检查一次
    let waitedTime = 0;
    
    while (window.googleMapsLoadStatus !== 'loaded' && waitedTime < maxWaitTime) {
        if (window.googleMapsLoadStatus === 'failed') {
            logger.error('❌ Google Maps API 加载失败，无法显示街景');
            return;
        }
        
        if (waitedTime === 0) {
            logger.info('⏳ 等待Google Maps API加载...');
        }
        
        await new Promise(resolve => setTimeout(resolve, checkInterval));
        waitedTime += checkInterval;
    }
    
    if (window.googleMapsLoadStatus !== 'loaded') {
        logger.error('❌ Google Maps API 加载超时');
        return;
    }

    // 检查Google Maps API是否已加载
    if (!initGoogleMapsAPI()) {
        logger.warning('⚠️ 跳过街景显示：Google Maps API未正确初始化');
        return;
    }

    // 检查位置坐标是否有效
    if (!scene.latitude || !scene.longitude) {
        logger.warning('⚠️ 跳过街景显示：场景位置坐标无效');
        return;
    }

    const location = {
        lat: parseFloat(scene.latitude),
        lng: parseFloat(scene.longitude)
    };

    // 保存当前场景信息
    currentStreetViewLocation = {
        scene: scene,
        location: location
    };

    logger.info(`🏙️ 开始为 ${scene.name} 加载街景...`);

    // 显示街景模态框
    showStreetViewModal(scene);

    // 尝试多个搜索半径查找街景数据
    async function tryFindStreetView() {
        const searchRadii = [500, 1000, 2000, 5000]; // 逐步扩大搜索半径
        
        for (let i = 0; i < searchRadii.length; i++) {
            const radius = searchRadii[i];
            logger.info(`🔍 搜索半径 ${radius}m 内的街景数据...`);
            
            try {
                const result = await streetViewService.getPanorama({
                    location: location,
                    radius: radius,
                    source: google.maps.StreetViewSource.OUTDOOR
                });
                
                if (result.data && result.data.location) {
                    logger.success(`✅ 在 ${radius}m 半径内找到街景数据`);
                    displayStreetViewPanorama(result.data, scene);
                    return; // 找到了，退出函数
                }
            } catch (error) {
                logger.info(`半径 ${radius}m 搜索失败: ${error.message}`);
                
                // 如果是ZERO_RESULTS，继续尝试更大半径
                if (error.code === 'ZERO_RESULTS' && i < searchRadii.length - 1) {
                    continue;
                }
                
                // 其他错误或最后一次尝试失败
                if (i === searchRadii.length - 1) {
                    logger.error(`❌ 所有搜索半径都失败: ${error.message}`);
                    showStreetViewError(`街景加载失败: ${error.message}`, 'API_ERROR');
                    return;
                }
            }
        }
        
        // 所有半径都没找到街景数据
        logger.warning('⚠️ 在所有搜索半径内都未找到街景数据');
        showStreetViewError('该位置附近暂无街景数据', 'NO_STREET_VIEW');
    }
    
    // 执行搜索
    tryFindStreetView();
}

// 显示街景模态框
function showStreetViewModal(scene) {
    const modal = document.getElementById('streetviewModal');
    const overlay = document.getElementById('streetviewOverlay');
    const title = document.getElementById('streetviewTitle');

    if (modal && overlay && title) {
        // 更新标题
        title.textContent = `🏙️ ${scene.name} - 街景视图`;

        // 显示模态框和遮罩
        modal.style.display = 'block';
        overlay.style.display = 'block';

        // 显示加载状态
        showStreetViewLoading();

        // 添加ESC键关闭功能
        document.addEventListener('keydown', handleStreetViewKeydown);

        logger.info('🏙️ 街景模态框已显示');
    }
}

// 显示街景全景图
function displayStreetViewPanorama(streetViewData, scene) {
    const container = document.getElementById('streetviewContainer');
    if (!container) {
        logger.error('❌ 找不到街景容器');
        return;
    }

    // 隐藏加载状态
    hideStreetViewLoading();

    try {
        // 创建Street View全景图
        streetViewPanorama = new google.maps.StreetViewPanorama(container, {
            position: streetViewData.location.latLng,
            pov: {
                heading: 0,
                pitch: 0
            },
            zoom: 1,
            enableCloseButton: false,
            addressControl: false,
            fullscreenControl: false,
            linksControl: true,
            panControl: true,
            zoomControl: true,
            motionTracking: false,
            motionTrackingControl: false
        });

        // 更新信息显示
        updateStreetViewInfo(streetViewData, scene);

        // 监听全景图事件
        streetViewPanorama.addListener('pano_changed', () => {
            logger.info('📍 街景全景图已更改');
        });

        streetViewPanorama.addListener('position_changed', () => {
            const position = streetViewPanorama.getPosition();
            if (position) {
                logger.info(`📍 街景位置已更改: ${position.lat()}, ${position.lng()}`);
            }
        });

        logger.success(`✅ ${scene.name} 街景加载成功`);

    } catch (error) {
        logger.error(`❌ 街景全景图创建失败: ${error.message}`);
        showStreetViewError(`创建街景失败: ${error.message}`, 'PANORAMA_ERROR');
    }
}

// 更新街景信息显示
function updateStreetViewInfo(streetViewData, scene) {
    const locationEl = document.getElementById('streetviewLocation');
    const coordsEl = document.getElementById('streetviewCoords');
    const dateEl = document.getElementById('streetviewDate');

    if (locationEl) {
        locationEl.textContent = scene.name || '未知位置';
    }

    if (coordsEl && streetViewData.location && streetViewData.location.latLng) {
        const lat = streetViewData.location.latLng.lat();
        const lng = streetViewData.location.latLng.lng();
        coordsEl.textContent = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    }

    if (dateEl && streetViewData.imageDate) {
        const date = new Date(streetViewData.imageDate);
        dateEl.textContent = date.toLocaleDateString('zh-CN');
    }
}

// 显示加载状态
function showStreetViewLoading() {
    const loadingEl = document.getElementById('streetviewLoading');
    const errorEl = document.getElementById('streetviewError');

    if (loadingEl) loadingEl.style.display = 'block';
    if (errorEl) errorEl.style.display = 'none';
}

// 隐藏加载状态
function hideStreetViewLoading() {
    const loadingEl = document.getElementById('streetviewLoading');
    if (loadingEl) loadingEl.style.display = 'none';
}

// 显示街景错误
function showStreetViewError(message, errorType) {
    hideStreetViewLoading();

    const errorEl = document.getElementById('streetviewError');
    const errorTextEl = document.getElementById('streetviewErrorText');

    if (errorEl) {
        errorEl.style.display = 'block';

        if (errorTextEl) {
            // 根据错误类型提供更友好的错误信息
            let friendlyMessage = message;
            
            if (errorType === 'NO_STREET_VIEW' || message.includes('ZERO_RESULTS')) {
                friendlyMessage = '该位置暂无街景数据，这在某些地区是正常现象。您可以尝试：\n• 选择附近的其他地点\n• 使用地图查看该区域\n• 继续探索其他有趣的地方';
            } else if (errorType === 'API_ERROR' && message.includes('unsupported_country_region_territory')) {
                friendlyMessage = '该地区的街景服务暂时不可用。这可能是由于地理位置限制导致的。';
            } else if (errorType === 'PANORAMA_ERROR') {
                friendlyMessage = '街景加载遇到技术问题，请稍后重试。';
            }
            
            errorTextEl.textContent = friendlyMessage;
        }

        logger.warning(`⚠️ 街景错误: ${message} (${errorType})`);
        
        // 自动关闭街景模态框（延迟3秒）
        setTimeout(() => {
            if (errorType === 'NO_STREET_VIEW' || message.includes('ZERO_RESULTS')) {
                closeStreetView();
                showSuccess('💡 该地点暂无街景，但您可以继续探索其他功能！');
            }
        }, 3000);
    }
}

// 关闭街景模态框
function closeStreetView() {
    const modal = document.getElementById('streetviewModal');
    const overlay = document.getElementById('streetviewOverlay');

    if (modal) modal.style.display = 'none';
    if (overlay) overlay.style.display = 'none';

    // 清理街景实例
    if (streetViewPanorama) {
        streetViewPanorama = null;
    }

    // 重置全屏状态
    if (isStreetViewFullscreen) {
        toggleStreetViewFullscreen();
    }

    // 移除键盘事件监听
    document.removeEventListener('keydown', handleStreetViewKeydown);

    // 重置变量
    currentStreetViewLocation = null;

    logger.info('🏙️ 街景模态框已关闭');
}

// 重置街景视角
function resetStreetViewHeading() {
    if (streetViewPanorama) {
        streetViewPanorama.setPov({
            heading: 0,
            pitch: 0
        });
        logger.info('🧭 街景视角已重置');
    }
}

// 切换全屏模式
function toggleStreetViewFullscreen() {
    const modal = document.getElementById('streetviewModal');

    if (modal) {
        if (isStreetViewFullscreen) {
            modal.classList.remove('fullscreen');
            isStreetViewFullscreen = false;
            logger.info('🔽 已退出全屏模式');
        } else {
            modal.classList.add('fullscreen');
            isStreetViewFullscreen = true;
            logger.info('🔼 已进入全屏模式');
        }
    }
}

// 分享街景位置
function shareStreetView() {
    if (currentStreetViewLocation && navigator.share) {
        const shareData = {
            title: `${currentStreetViewLocation.scene.name} - 街景视图`,
            text: `查看 ${currentStreetViewLocation.scene.name} 的街景`,
            url: `https://www.google.com/maps/@${currentStreetViewLocation.location.lat},${currentStreetViewLocation.location.lng},3a,75y,90t/data=!3m8!1e2!3m6!1s!2s!3s!4s!5s!6s`
        };

        navigator.share(shareData)
            .then(() => logger.info('📤 街景位置已分享'))
            .catch((error) => logger.warning(`⚠️ 分享失败: ${error.message}`));
    } else if (currentStreetViewLocation) {
        // 复制到剪贴板
        const shareUrl = `https://www.google.com/maps/@${currentStreetViewLocation.location.lat},${currentStreetViewLocation.location.lng},3a,75y,90t/data=!3m8!1e2!3m6!1s!2s!3s!4s!5s!6s`;
        navigator.clipboard.writeText(shareUrl)
            .then(() => {
                showSuccess('📤 街景链接已复制到剪贴板');
                logger.info('📤 街景链接已复制');
            })
            .catch((error) => logger.warning(`⚠️ 复制失败: ${error.message}`));
    }
}

// 重试加载街景
function retryStreetView() {
    if (currentStreetViewLocation) {
        logger.info('🔄 重试加载街景...');
        
        // 隐藏错误信息，显示加载状态
        const errorEl = document.getElementById('streetviewError');
        const loadingEl = document.getElementById('streetviewLoading');
        
        if (errorEl) errorEl.style.display = 'none';
        if (loadingEl) loadingEl.style.display = 'block';
        
        // 稍微调整坐标，尝试附近位置
        const originalScene = currentStreetViewLocation.scene;
        const adjustedScenes = [
            originalScene, // 原始位置
            { // 向北偏移
                ...originalScene,
                latitude: parseFloat(originalScene.latitude) + 0.001,
                name: originalScene.name + ' (北侧)'
            },
            { // 向南偏移
                ...originalScene,
                latitude: parseFloat(originalScene.latitude) - 0.001,
                name: originalScene.name + ' (南侧)'
            },
            { // 向东偏移
                ...originalScene,
                longitude: parseFloat(originalScene.longitude) + 0.001,
                name: originalScene.name + ' (东侧)'
            },
            { // 向西偏移
                ...originalScene,
                longitude: parseFloat(originalScene.longitude) - 0.001,
                name: originalScene.name + ' (西侧)'
            }
        ];
        
        // 尝试每个调整后的位置
        tryMultipleLocations(adjustedScenes, 0);
    }
}

// 尝试多个位置的街景
async function tryMultipleLocations(scenes, index) {
    if (index >= scenes.length) {
        logger.warning('⚠️ 所有位置都无法加载街景');
        showStreetViewError('该区域暂无可用的街景数据', 'NO_STREET_VIEW');
        return;
    }
    
    const scene = scenes[index];
    logger.info(`🔍 尝试位置 ${index + 1}/${scenes.length}: ${scene.name}`);
    
    try {
        const location = {
            lat: parseFloat(scene.latitude),
            lng: parseFloat(scene.longitude)
        };
        
        const result = await streetViewService.getPanorama({
            location: location,
            radius: 2000, // 使用较大的搜索半径
            source: google.maps.StreetViewSource.OUTDOOR
        });
        
        if (result.data && result.data.location) {
            logger.success(`✅ 在位置 "${scene.name}" 找到街景数据`);
            displayStreetViewPanorama(result.data, scene);
        } else {
            // 尝试下一个位置
            setTimeout(() => tryMultipleLocations(scenes, index + 1), 500);
        }
    } catch (error) {
        logger.info(`位置 "${scene.name}" 失败: ${error.message}`);
        // 尝试下一个位置
        setTimeout(() => tryMultipleLocations(scenes, index + 1), 500);
    }
}

// 处理键盘事件
function handleStreetViewKeydown(event) {
    if (event.key === 'Escape') {
        closeStreetView();
    } else if (event.key === 'f' || event.key === 'F') {
        toggleStreetViewFullscreen();
    } else if (event.key === 'r' || event.key === 'R') {
        resetStreetViewHeading();
    }
}

// 页面加载完成后初始化Google Maps
window.addEventListener('load', function() {
    // 等待Google Maps API加载
    if (typeof window.initGoogleMaps === 'function') {
        window.initGoogleMaps();
    }
});

// 打开街景视图的入口函数
function openStreetView(latitude, longitude, placeName) {
    if (!latitude || !longitude) {
        logger.error('❌ 街景打开失败：缺少有效的坐标信息');
        showError('无法打开街景：坐标信息无效');
        return;
    }
    
    logger.info(`🏙️ 打开街景: ${placeName} (${latitude}, ${longitude})`);
    
    // 创建场景对象
    const scene = {
        name: placeName || '未知地点',
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude)
    };
    
    // 调用现有的街景显示函数
    showStreetViewForLocation(scene);
}

// 全局暴露街景函数
window.openStreetView = openStreetView;
window.closeStreetView = closeStreetView;
window.resetStreetViewHeading = resetStreetViewHeading;
window.toggleStreetViewFullscreen = toggleStreetViewFullscreen;
window.shareStreetView = shareStreetView;
window.retryStreetView = retryStreetView;

// 清理结果显示
function clearResults() {
    const container = document.getElementById('placesContainer');
    if (container) {
        container.innerHTML = '';
    }
    
    // 清理到达确认界面
    const confirmationDiv = document.getElementById('arrivalConfirmation');
    if (confirmationDiv) {
        confirmationDiv.remove();
    }
    
    // 隐藏历史记录区域
    const historySection = document.getElementById('journeyHistorySection');
    if (historySection) {
        historySection.style.display = 'none';
    }
    
    logger.info('🧹 已清理探索结果显示');
}

// 全球城市数据库相关变量
let allCities = [];
let selectedCity = null;

// 初始化城市数据库
async function initializeCityDatabase() {
    try {
        const response = await fetch(`${getAPIBaseURL()}/api/cities`);
        if (response.ok) {
            allCities = await response.json();
            populateCitySelector();
            logger.info(`✅ 成功加载 ${allCities.length} 个城市信息`);
        } else {
            throw new Error('加载城市数据失败');
        }
    } catch (error) {
        logger.error(`❌ 初始化城市数据库失败: ${error.message}`);
    }
}

// 城市漫游功能实现
async function confirmRoaming() {
    const countryInput = document.getElementById('roamingCountry');
    const cityInput = document.getElementById('roamingCity');
    const placeInput = document.getElementById('roamingPlace');
    const statusDiv = document.getElementById('roamingStatus');
    
    // 获取输入值
    const country = countryInput.value.trim();
    const city = cityInput.value.trim();
    const place = placeInput.value.trim();
    
    // 验证输入
    if (!country && !city && !place) {
        alert('请至少填写一个位置信息（国家、城市或景点）');
        return;
    }
    
    // 构建搜索查询
    const searchQuery = [country, city, place].filter(Boolean).join(', ');
    logger.info(`🌍 开始漫游搜索: "${searchQuery}"`);
    
    // 显示加载状态
    statusDiv.style.display = 'flex';
    statusDiv.innerHTML = `
        <div class="loading-spinner"></div>
        <span>正在搜索 "${searchQuery}"...</span>
    `;
    
    try {
        // 调用Google Maps地理编码API
        const geocodeResult = await geocodeLocation(searchQuery);
        
        if (geocodeResult.success) {
            const locationData = geocodeResult.data;
            logger.success(`✅ 找到位置: ${locationData.formatted_address}`);
            
            // 立即隐藏加载状态
            statusDiv.style.display = 'none';
            
            // 获取地点详细信息
            const placeDetails = await getPlaceDetails(locationData);
            
            // 执行漫游跳转
            await executeRoaming(locationData, placeDetails);
            
            // 清空输入框
            countryInput.value = '';
            cityInput.value = '';
            placeInput.value = '';
            
            // 关闭设置面板
            const settingsPanel = document.getElementById('settingsPanel');
            if (settingsPanel) {
                settingsPanel.classList.remove('show');
            }
            
        } else {
            throw new Error(geocodeResult.error || '未找到指定位置');
        }
        
    } catch (error) {
        logger.error(`❌ 漫游失败: ${error.message}`);
        statusDiv.innerHTML = `
            <span style="color: #e53e3e;">❌ ${error.message}</span>
        `;
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 3000);
    }
}

// 填充城市选择器
function populateCitySelector() {
    const selector = document.getElementById('citySelector');
    if (!selector) return;
    
    // 清空现有选项（保留默认选项和optgroup标签）
    const globalGroup = selector.querySelector('optgroup[label="🌍 全球知名城市"]');
    const chinaGroup = selector.querySelector('optgroup[label="🇨🇳 中国知名城市"]');
    
    if (globalGroup) globalGroup.innerHTML = '';
    if (chinaGroup) chinaGroup.innerHTML = '';
    
    // 分类添加城市选项
    allCities.forEach(city => {
        const option = document.createElement('option');
        option.value = city.key;
        option.textContent = `${city.name} (${city.attraction_count}个景点)`;
        
        if (city.type === 'global' && globalGroup) {
            globalGroup.appendChild(option);
        } else if (city.type === 'china' && chinaGroup) {
            chinaGroup.appendChild(option);
        }
    });
}

// 城市选择事件处理
function onCitySelected() {
    const selector = document.getElementById('citySelector');
    const cityKey = selector.value;
    
    if (!cityKey) {
        hideSelectedCityInfo();
        return;
    }
    
    const city = allCities.find(c => c.key === cityKey);
    if (city) {
        selectedCity = city;
        showSelectedCityInfo(city);
        logger.info(`🏙️ 选择城市: ${city.name}`);
    }
}

// 显示选中城市信息
function showSelectedCityInfo(city) {
    const infoDiv = document.getElementById('selectedCityInfo');
    const nameEl = document.getElementById('selectedCityName');
    const detailsEl = document.getElementById('selectedCityDetails');
    
    if (infoDiv && nameEl && detailsEl) {
        const countryFlag = city.country === '中国' ? '🇨🇳' : 
                          city.country === '法国' ? '🇫🇷' :
                          city.country === '英国' ? '🇬🇧' :
                          city.country === '意大利' ? '🇮🇹' :
                          city.country === '美国' ? '🇺🇸' :
                          city.country === '日本' ? '🇯🇵' :
                          city.country === '西班牙' ? '🇪🇸' :
                          city.country === '泰国' ? '🇹🇭' :
                          city.country === '土耳其' ? '🇹🇷' : '🌍';
        
        nameEl.textContent = `${countryFlag} ${city.name}`;
        detailsEl.textContent = `${city.country} | ${city.attraction_count} 个知名景点`;
        infoDiv.style.display = 'block';
    }
}

// 隐藏选中城市信息
function hideSelectedCityInfo() {
    const infoDiv = document.getElementById('selectedCityInfo');
    if (infoDiv) {
        infoDiv.style.display = 'none';
    }
    selectedCity = null;
}

// 城市搜索功能
async function searchCities() {
    const searchInput = document.getElementById('citySearch');
    const resultsDiv = document.getElementById('searchResults');
    const query = searchInput.value.trim();
    
    if (!query) {
        resultsDiv.style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch(`${getAPIBaseURL()}/api/cities/search?query=${encodeURIComponent(query)}`);
        if (response.ok) {
            const data = await response.json();
            displaySearchResults(data.cities);
        }
    } catch (error) {
        logger.error(`搜索城市失败: ${error.message}`);
    }
}

// 显示搜索结果
function displaySearchResults(cities) {
    const resultsDiv = document.getElementById('searchResults');
    
    if (!cities || cities.length === 0) {
        resultsDiv.style.display = 'none';
        return;
    }
    
    resultsDiv.innerHTML = '';
    cities.forEach(city => {
        const item = document.createElement('div');
        item.className = 'search-result-item';
        item.onclick = () => selectSearchResult(city);
        
        const countryFlag = city.country === '中国' ? '🇨🇳' : 
                          city.country === '法国' ? '🇫🇷' :
                          city.country === '英国' ? '🇬🇧' :
                          city.country === '意大利' ? '🇮🇹' :
                          city.country === '美国' ? '🇺🇸' :
                          city.country === '日本' ? '🇯🇵' :
                          city.country === '西班牙' ? '🇪🇸' :
                          city.country === '泰国' ? '🇹🇭' :
                          city.country === '土耳其' ? '🇹🇷' : '🌍';
        
        item.innerHTML = `
            <div class="search-result-city">${countryFlag} ${city.name}</div>
            <div class="search-result-country">${city.country}</div>
            <div class="search-result-attractions">${city.attraction_count} 个景点</div>
        `;
        
        resultsDiv.appendChild(item);
    });
    
    resultsDiv.style.display = 'block';
}

// 选择搜索结果
function selectSearchResult(city) {
    const selector = document.getElementById('citySelector');
    const searchInput = document.getElementById('citySearch');
    const resultsDiv = document.getElementById('searchResults');
    
    // 更新选择器
    selector.value = city.key;
    searchInput.value = '';
    resultsDiv.style.display = 'none';
    
    // 显示城市信息
    selectedCity = city;
    showSelectedCityInfo(city);
}

// 搜索输入回车处理
function handleSearchEnter(event) {
    if (event.key === 'Enter') {
        const resultsDiv = document.getElementById('searchResults');
        const firstResult = resultsDiv.querySelector('.search-result-item');
        if (firstResult) {
            firstResult.click();
        }
    }
}

// 查看城市景点
async function showCityAttractions() {
    if (!selectedCity) return;
    
    const statusDiv = document.getElementById('roamingStatus');
    const statusText = document.getElementById('roamingStatusText');
    
    statusDiv.style.display = 'flex';
    statusText.textContent = `正在加载 ${selectedCity.name} 的景点信息...`;
    
    try {
        const response = await fetch(`${getAPIBaseURL()}/api/cities/${selectedCity.key}/attractions`);
        if (response.ok) {
            const attractions = await response.json();
            displayCityAttractions(selectedCity, attractions);
            
            // 关闭设置面板
            const settingsPanel = document.getElementById('settingsPanel');
            if (settingsPanel) {
                settingsPanel.classList.remove('show');
            }
        } else {
            throw new Error('获取景点信息失败');
        }
    } catch (error) {
        logger.error(`获取景点信息失败: ${error.message}`);
        statusText.textContent = `❌ ${error.message}`;
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 3000);
        return;
    }
    
    statusDiv.style.display = 'none';
}

// 随机漫游到景点
async function roamToRandomAttraction() {
    if (!selectedCity) return;
    
    const statusDiv = document.getElementById('roamingStatus');
    const statusText = document.getElementById('roamingStatusText');
    
    statusDiv.style.display = 'flex';
    statusText.textContent = `正在随机选择 ${selectedCity.name} 的景点...`;
    
    try {
        const response = await fetch(`${getAPIBaseURL()}/api/cities/roam`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                city_key: selectedCity.key
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success) {
                await executeAttractionRoaming(result.attraction);
                
                // 关闭设置面板
                const settingsPanel = document.getElementById('settingsPanel');
                if (settingsPanel) {
                    settingsPanel.classList.remove('show');
                }
            } else {
                throw new Error(result.message);
            }
        } else {
            throw new Error('随机漫游请求失败');
        }
    } catch (error) {
        logger.error(`随机漫游失败: ${error.message}`);
        statusText.textContent = `❌ ${error.message}`;
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 3000);
        return;
    }
    
    statusDiv.style.display = 'none';
}

// 漫游到指定景点
async function roamToAttraction(cityKey, attractionIndex) {
    try {
        const response = await fetch(`${getAPIBaseURL()}/api/cities/${cityKey}/attractions`);
        if (response.ok) {
            const attractions = await response.json();
            const attraction = attractions[attractionIndex];
            if (attraction) {
                await executeAttractionRoaming(attraction);
            }
        }
    } catch (error) {
        logger.error(`漫游到景点失败: ${error.message}`);
    }
}

// 执行景点漫游
async function executeAttractionRoaming(attraction) {
    logger.info(`🚀 执行漫游到: ${attraction.name}`);
    
    // 更新当前位置
    currentPosition = {
        latitude: attraction.latitude,
        longitude: attraction.longitude,
        accuracy: 10,
        altitude: null,
        altitudeAccuracy: null,
        heading: null,
        speed: null,
        timestamp: Date.now()
    };
    
    // 更新位置显示
    updateLocationDisplayForAttraction(attraction);
    
    // 显示漫游成功信息
    showAttractionRoamingSuccess(attraction);
    
    // 重置探索状态
    resetExplorationState();
    
    // 🆕 自动搜索附近景点并按距离排序
    await searchNearbyAttractions(attraction);
    
    logger.success(`✅ 漫游成功! 当前位置: ${attraction.name}`);
}

// 🆕 搜索附近景点并按距离排序
async function searchNearbyAttractions(currentAttraction) {
    logger.info(`🔍 搜索 ${currentAttraction.name} 附近的景点...`);
    
    try {
        // 使用默认角度（0度，正北方向）搜索附近景点
        const searchData = {
            latitude: currentAttraction.latitude,
            longitude: currentAttraction.longitude,
            heading: 0, // 默认正北方向
            segment_distance: settings.segmentDistance,
            time_mode: settings.timeMode
        };
        
        const response = await fetch(`${getAPIBaseURL()}/api/explore-real`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(searchData)
        });
        
        if (response.ok) {
            const data = await response.json();
            let places = data.places || [];
            
            // 将当前景点添加到列表开头
            const currentPlace = {
                name: currentAttraction.name,
                latitude: currentAttraction.latitude,
                longitude: currentAttraction.longitude,
                description: currentAttraction.description || '当前所在景点',
                category: currentAttraction.category || '景点',
                opening_hours: currentAttraction.opening_hours || '全天开放',
                ticket_price: currentAttraction.ticket_price || '免费',
                reservation_method: currentAttraction.reservation_method || '无需预约',
                distance: 0, // 当前景点距离为0
                isCurrentLocation: true // 标记为当前位置
            };
            
            // 将当前景点放在第一位
            places.unshift(currentPlace);
            
            // 按距离排序（当前景点已经在第一位）
            places.sort((a, b) => {
                if (a.isCurrentLocation) return -1; // 当前景点始终在第一位
                if (b.isCurrentLocation) return 1;
                return (a.distance || 0) - (b.distance || 0);
            });
            
            // 显示搜索结果
            displayPlaces(places);
            
            logger.success(`✅ 找到 ${places.length} 个附近景点，已按距离排序`);
        } else {
            logger.error('搜索附近景点失败');
        }
    } catch (error) {
        logger.error(`搜索附近景点时出错: ${error.message}`);
    }
}

// 更新景点位置显示
function updateLocationDisplayForAttraction(attraction) {
    // 更新坐标显示
    const coordinatesEl = document.getElementById('coordinates');
    if (coordinatesEl) {
        coordinatesEl.textContent = `${attraction.latitude.toFixed(6)}, ${attraction.longitude.toFixed(6)}`;
    }
    
    // 更新位置名称
    const currentLocationEl = document.getElementById('currentLocation');
    if (currentLocationEl) {
        currentLocationEl.textContent = `${attraction.name} - ${attraction.city}`;
    }
    
    // 更新精度显示
    const accuracyEl = document.getElementById('accuracy');
    if (accuracyEl) {
        accuracyEl.textContent = '±10m (漫游)';
    }
    
    // 更新位置状态
    const locationStatusEl = document.getElementById('locationStatus');
    if (locationStatusEl) {
        locationStatusEl.textContent = '✅ 漫游定位';
        locationStatusEl.className = 'status-success';
    }
}

// 显示景点漫游成功信息
function showAttractionRoamingSuccess(attraction) {
    const container = document.getElementById('placesContainer');
    if (!container) return;
    
    // 清空现有内容
    container.innerHTML = '';
    
    // 创建漫游成功卡片
    const successCard = document.createElement('div');
    successCard.className = 'roaming-success-card';
    
    successCard.innerHTML = `
        <div class="roaming-header">
            <h3>🎉 漫游成功!</h3>
            <div class="location-info">
                <h4>📍 ${attraction.name}</h4>
                <p class="coordinates">坐标: ${attraction.latitude.toFixed(6)}, ${attraction.longitude.toFixed(6)}</p>
                <p class="location-details">${attraction.city} | ${attraction.category}</p>
            </div>
        </div>
        
        <div class="place-details">
            ${attraction.image ? `
                <img src="${attraction.image}" alt="${attraction.name}" class="place-photo" 
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNiIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuaaguaXoOWbvueJhzwvdGV4dD48L3N2Zz4='"
            ` : ''}
            
            <p class="place-description">${attraction.description}</p>
            
            <div class="attraction-details">
                <div class="detail-item">
                    <strong>⏰ 开放时间:</strong> ${attraction.opening_hours}
                </div>
                <div class="detail-item">
                    <strong>💰 门票价格:</strong> ${attraction.ticket_price}
                </div>
                <div class="detail-item">
                    <strong>📝 预约方式:</strong> ${attraction.booking_method}
                </div>
            </div>
        </div>
        
        <div class="roaming-actions">
            <button class="explore-btn" onclick="startExplorationFromHere()">🧭 从这里开始探索</button>
            ${attraction.video ? `
                <button class="action-btn" onclick="playVideo('${attraction.video}', '${attraction.name}')">
                    🎥 观看视频
                </button>
            ` : ''}
        </div>
    `;
    
    container.appendChild(successCard);
}

// 显示城市景点列表
function displayCityAttractions(city, attractions) {
    const container = document.getElementById('placesContainer');
    if (!container) return;
    
    container.innerHTML = `
        <div class="city-attractions-header" style="
            text-align: center;
            margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        ">
            <h2 style="color: #4a5568; margin-bottom: 10px;">🏛️ ${city.name} 知名景点</h2>
            <p style="color: #718096; font-size: 1.1em;">${city.country} | 共 ${attractions.length} 个景点</p>
        </div>
    `;
    
    attractions.forEach((attraction, index) => {
        const attractionCard = createAttractionCard(attraction, index);
        container.appendChild(attractionCard);
    });
    
    logger.info(`✅ 显示 ${city.name} 的 ${attractions.length} 个景点`);
}

// 创建景点卡片
function createAttractionCard(attraction, index) {
    const card = document.createElement('div');
    card.className = 'place-card attraction-card';
    
    card.innerHTML = `
        <div class="place-media">
            ${attraction.image ? `
                <img src="${attraction.image}" alt="${attraction.name}" class="place-image" 
                     onerror="this.src='data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZjBmMGYwIi8+PHRleHQgeD0iNTAlIiB5PSI1MCUiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNiIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPuaaguaXoOWbvueJhzwvdGV4dD48L3N2Zz4='"
            ` : `
                <div class="place-image-placeholder" style="
                    width: 100%;
                    height: 200px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    color: white;
                ">
                    <span style="font-size: 3rem; margin-bottom: 10px;">📸</span>
                    <p>暂无图片</p>
                </div>
            `}
            ${attraction.video ? `
                <div class="video-overlay" onclick="playVideo('${attraction.video}', '${attraction.name}')">
                    <div class="play-button">▶️</div>
                </div>
            ` : ''}
        </div>
        
        <div class="place-content">
            <h3 class="place-name">${attraction.name}</h3>
            
            <div class="place-location-info">
                📍 ${attraction.latitude.toFixed(4)}°, ${attraction.longitude.toFixed(4)}°
                | ${attraction.country} - ${attraction.city}
            </div>
            
            <p class="place-description">${attraction.description}</p>
            
            <div class="attraction-details" style="
                background: rgba(102, 126, 234, 0.1);
                border-radius: 8px;
                padding: 15px;
                margin: 15px 0;
                font-size: 0.9em;
            ">
                <div class="detail-item" style="margin-bottom: 8px;">
                    <strong>🏷️ 类别:</strong> ${attraction.category}
                </div>
                <div class="detail-item" style="margin-bottom: 8px;">
                    <strong>⏰ 开放时间:</strong> ${attraction.opening_hours}
                </div>
                <div class="detail-item" style="margin-bottom: 8px;">
                    <strong>💰 门票价格:</strong> ${attraction.ticket_price}
                </div>
                <div class="detail-item">
                    <strong>📝 预约方式:</strong> ${attraction.booking_method}
                </div>
            </div>
            
            <div class="place-actions">
                <button class="action-btn primary" onclick="roamToAttraction('${selectedCity.key}', ${index})">
                    🧭 ${t('exploreHere')}
                </button>
                ${attraction.video ? `
                    <button class="action-btn" onclick="playVideo('${attraction.video}', '${attraction.name}')">
                        🎥 观看视频
                    </button>
                ` : ''}
            </div>
        </div>
    `;
    
    return card;
}

// 地理编码API调用
async function geocodeLocation(query) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/geocode`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                language: 'zh-CN'
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        return result;
        
    } catch (error) {
        logger.error(`地理编码API调用失败: ${error.message}`);
        return {
            success: false,
            error: `无法连接到地理编码服务: ${error.message}`
        };
    }
}

// 获取地点详细信息
async function getPlaceDetails(locationData) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/place-details`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                place_id: locationData.place_id,
                location: {
                    lat: locationData.geometry.location.lat,
                    lng: locationData.geometry.location.lng
                }
            })
        });
        
        if (response.ok) {
            const result = await response.json();
            return result.success ? result.data : null;
        }
        
    } catch (error) {
        logger.warning(`获取地点详情失败: ${error.message}`);
    }
    
    return null;
}

// 执行漫游跳转
async function executeRoaming(locationData, placeDetails) {
    const location = locationData.geometry.location;
    
    logger.info(`🚀 执行漫游到: ${locationData.formatted_address}`);
    
    // 更新当前位置
    currentPosition = {
        latitude: location.lat,
        longitude: location.lng,
        accuracy: 10, // 高精度
        altitude: null,
        altitudeAccuracy: null,
        heading: null,
        speed: null,
        timestamp: Date.now()
    };
    
    // 同时更新window对象以确保兼容性
    window.currentPosition = currentPosition;
    
    // 更新UI显示
    updateLocationDisplay(locationData, placeDetails);
    
    // 显示漫游成功信息
    showRoamingSuccess(locationData, placeDetails);
    
    // 重置探索状态
    resetExplorationState();
    
    logger.success(`✅ 漫游成功! 当前位置: ${locationData.formatted_address}`);
}

// 更新位置显示
function updateLocationDisplay(locationData, placeDetails) {
    const location = locationData.geometry.location;
    
    // 更新坐标显示
    const coordinatesEl = document.getElementById('coordinates');
    if (coordinatesEl) {
        coordinatesEl.textContent = `${location.lat.toFixed(6)}, ${location.lng.toFixed(6)}`;
    }
    
    // 更新位置名称
    const currentLocationEl = document.getElementById('currentLocation');
    if (currentLocationEl) {
        currentLocationEl.textContent = locationData.formatted_address;
    }
    
    // 更新精度显示
    const accuracyEl = document.getElementById('accuracy');
    if (accuracyEl) {
        accuracyEl.textContent = '±10m (漫游)';
    }
    
    // 更新位置状态
    const locationStatusEl = document.getElementById('locationStatus');
    if (locationStatusEl) {
        locationStatusEl.textContent = '✅ 漫游定位';
        locationStatusEl.className = 'status-success';
    }
}

// 显示漫游成功信息
function showRoamingSuccess(locationData, placeDetails) {
    const container = document.getElementById('placesContainer');
    if (!container) return;
    
    // 清空现有内容
    container.innerHTML = '';
    
    // 创建漫游成功卡片
    const successCard = document.createElement('div');
    successCard.className = 'roaming-success-card';
    
    let cardContent = `
        <div class="roaming-header">
            <h3>🎉 漫游成功!</h3>
            <div class="location-info">
                <h4>📍 ${locationData.formatted_address}</h4>
                <p class="coordinates">坐标: ${locationData.geometry.location.lat.toFixed(6)}, ${locationData.geometry.location.lng.toFixed(6)}</p>
                <p class="location-type">位置类型: ${locationData.geometry.location_type || '精确位置'}</p>
            </div>
        </div>
    `;
    
    // 如果有地点详情，显示详细信息
    if (placeDetails) {
        cardContent += `
            <div class="place-details">
                <h4>🏛️ ${placeDetails.name || '未知地点'}</h4>
                ${placeDetails.rating ? `<div class="rating">⭐ 评分: ${placeDetails.rating}/5 (${placeDetails.user_ratings_total || 0}条评价)</div>` : ''}
                ${placeDetails.formatted_address ? `<div class="address">🏠 地址: ${placeDetails.formatted_address}</div>` : ''}
                ${placeDetails.formatted_phone_number ? `<div class="phone">📞 电话: ${placeDetails.formatted_phone_number}</div>` : ''}
                ${placeDetails.website ? `<div class="website"><a href="${placeDetails.website}" target="_blank">🌐 官方网站</a></div>` : ''}
                ${placeDetails.opening_hours ? `<div class="hours">🕒 营业时间: ${placeDetails.opening_hours.weekday_text ? placeDetails.opening_hours.weekday_text[0] : '营业时间未知'}</div>` : ''}
                ${placeDetails.editorial_summary ? `<div class="summary">📝 简介: ${placeDetails.editorial_summary.overview}</div>` : ''}
                ${placeDetails.types ? `<div class="types">🏷️ 类型: ${placeDetails.types.slice(0, 3).join(', ')}</div>` : ''}
            </div>
        `;
        
        // 显示照片
        if (placeDetails.photos && placeDetails.photos.length > 0) {
            cardContent += `
                <div class="place-photos">
                    <h5>📸 地点照片</h5>
                    <div class="photos-grid">
                        ${placeDetails.photos.slice(0, 3).map(photo => `
                            <img src="${photo.photo_url}" alt="地点照片" class="place-photo" onclick="showPhotoModal('${photo.photo_url}')">
                        `).join('')}
                    </div>
                </div>
            `;
        }
    }
    
    cardContent += `
        <div class="roaming-actions">
            <button class="explore-btn" onclick="startExplorationFromHere()">🧭 从这里开始探索</button>
        </div>
    `;
    
    successCard.innerHTML = cardContent;
    container.appendChild(successCard);
    
    // 滚动到结果区域
    container.scrollIntoView({ behavior: 'smooth' });
}

// 从当前位置开始探索
function startExplorationFromHere() {
    logger.info('🧭 从漫游位置开始探索');
    
    // 清空漫游结果
    const container = document.getElementById('placesContainer');
    if (container) {
        container.innerHTML = '';
    }
    
    // 如果有方向，直接开始探索
    if (window.currentHeading !== null && window.currentHeading !== undefined) {
        startExploration();
    } else {
        // 提示用户设置方向
        alert('请先设置探索方向，然后点击"开始探索"按钮');
    }
}

// 重置探索状态
function resetExplorationState() {
    // 清空地点容器
    const container = document.getElementById('placesContainer');
    if (container) {
        container.innerHTML = '';
    }
    
    // 重置旅程状态
    if (window.currentJourney) {
        window.currentJourney = null;
    }
    
    // 隐藏历史记录
    const historySection = document.getElementById('journeyHistorySection');
    if (historySection) {
        historySection.style.display = 'none';
    }
}

// 显示照片模态框
function showPhotoModal(photoUrl) {
    const modal = document.createElement('div');
    modal.className = 'photo-modal';
    modal.innerHTML = `
        <div class="photo-modal-content">
            <span class="photo-modal-close" onclick="closePhotoModal()">&times;</span>
            <img src="${photoUrl}" alt="地点照片" class="photo-modal-image">
        </div>
    `;
    
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closePhotoModal();
        }
    });
}

// 关闭照片模态框
function closePhotoModal() {
    const modal = document.querySelector('.photo-modal');
    if (modal) {
        modal.remove();
    }
}

window.startJourney = startJourney;
window.journeyManagement = journeyManagement;
window.setManualLocation = setManualLocation;
window.generateAndShowSceneReview = generateAndShowSceneReview;
window.clearResults = clearResults;
// 城市选择相关函数
window.onCitySelected = onCitySelected;
window.searchCities = searchCities;
window.handleSearchEnter = handleSearchEnter;
window.showCityAttractions = showCityAttractions;
window.roamToRandomAttraction = roamToRandomAttraction;
window.roamToAttraction = roamToAttraction;
window.confirmRoaming = confirmRoaming;
window.startExplorationFromHere = startExplorationFromHere;
window.showPhotoModal = showPhotoModal;
window.closePhotoModal = closePhotoModal;

// 视频播放功能
function playVideo(videoUrl, placeName) {
    // 创建视频模态框
    const modal = document.createElement('div');
    modal.className = 'video-modal';
    modal.innerHTML = `
        <div class="video-modal-content">
            <div class="video-modal-header">
                <h3>${placeName} - 视频介绍</h3>
                <button class="close-btn" onclick="closeVideoModal()">&times;</button>
            </div>
            <div class="video-container">
                <iframe 
                    src="${getEmbedUrl(videoUrl)}" 
                    frameborder="0" 
                    allowfullscreen
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture">
                </iframe>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 添加关闭事件
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeVideoModal();
        }
    });
}

function closeVideoModal() {
    const modal = document.querySelector('.video-modal');
    if (modal) {
        modal.remove();
    }
}

function getEmbedUrl(videoUrl) {
    // 转换YouTube URL为嵌入格式
    if (videoUrl.includes('youtube.com/watch?v=')) {
        const videoId = videoUrl.split('v=')[1].split('&')[0];
        return `https://www.youtube.com/embed/${videoId}`;
    } else if (videoUrl.includes('youtu.be/')) {
        const videoId = videoUrl.split('youtu.be/')[1].split('?')[0];
        return `https://www.youtube.com/embed/${videoId}`;
    }
    return videoUrl; // 如果已经是嵌入格式，直接返回
}

// 处理图片加载错误
function handleImageError(imgElement, placeName) {
    if (imgElement && !imgElement.src.startsWith('data:')) {
        imgElement.src = generatePlaceholderImage(placeName);
        logger.warning(`图片加载失败，使用占位图片: ${placeName}`);
    }
}

// 全局函数：触发文件上传（用于内联onclick）
window.triggerFileUpload = function(inputId) {
    const input = document.getElementById(inputId);
    if (input) {
        input.click();
        logger.info(`触发文件上传: ${inputId}`);
    } else {
        logger.error(`找不到文件输入元素: ${inputId}`);
    }
}

// 强制启用生成按钮
function forceEnableGenerateButton() {
    // 尝试查找不同的生成按钮ID（兼容新旧版本）
    const generateBtn = document.getElementById('attractionGenerateBtn') || document.getElementById('generateBtn');
    logger.info(`🔍 查找生成按钮: ${generateBtn ? '找到' : '未找到'}`);
    
    if (generateBtn) {
        // 记录按钮当前状态
        logger.info(`📊 按钮当前状态: disabled=${generateBtn.disabled}, onclick="${generateBtn.onclick}", className="${generateBtn.className}"`);
        
        // 强制移除所有禁用属性和样式
        generateBtn.disabled = false;
        generateBtn.removeAttribute('disabled');
        generateBtn.style.opacity = '1';
        generateBtn.style.cursor = 'pointer';
        generateBtn.style.backgroundColor = '#667eea';
        generateBtn.style.color = 'white';
        generateBtn.style.pointerEvents = 'auto';
        generateBtn.style.userSelect = 'auto';
        generateBtn.style.filter = 'none';
        
        // 移除所有可能的禁用类
        generateBtn.classList.remove('disabled');
        generateBtn.classList.remove('btn-disabled');
        generateBtn.classList.remove('generate-btn-disabled');
        
        // 添加启用类
        generateBtn.classList.add('generate-btn-enabled');
        
        // 检查文件是否已选择
        if (window.selectedPhotoFile) {
            logger.info(`✅ 已选择文件: ${window.selectedPhotoFile.name}`);
        } else {
            logger.warning('⚠️ 未选择文件，但仍然启用按钮');
        }
        
        // 验证启用结果
        setTimeout(() => {
            const stillDisabled = generateBtn.disabled;
            const computedStyle = window.getComputedStyle(generateBtn);
            logger.info(`✅ 启用验证: disabled=${stillDisabled}, cursor=${computedStyle.cursor}, pointer-events=${computedStyle.pointerEvents}`);
            
            if (stillDisabled || computedStyle.pointerEvents === 'none' || computedStyle.cursor === 'not-allowed') {
                logger.error('❌ 按钮仍然无法点击，尝试强制修复');
                generateBtn.style.cssText = 'cursor: pointer !important; pointer-events: auto !important; opacity: 1 !important; background-color: #667eea !important; color: white !important;';
            }
        }, 10);
        
        logger.success('🎯 强制启用生成按钮完成');
        return true;
    } else {
        logger.error('❌ 找不到生成按钮，尝试延迟启用');
        setTimeout(forceEnableGenerateButton, 100);
        return false;
    }
}

// 全局函数：手动启用生成按钮（调试用）
window.enableGenerateButton = function() {
    return forceEnableGenerateButton();
}

// 全局函数：调试按钮状态
window.debugGenerateButton = function() {
    const generateBtn = document.getElementById('attractionGenerateBtn');
    if (generateBtn) {
        console.log('=== 生成按钮调试信息 ===');
        console.log('按钮元素:', generateBtn);
        console.log('disabled属性:', generateBtn.disabled);
        console.log('onclick属性:', generateBtn.getAttribute('onclick'));
        console.log('onclick函数:', generateBtn.onclick);
        console.log('style.cursor:', generateBtn.style.cursor);
        console.log('style.pointerEvents:', generateBtn.style.pointerEvents);
        console.log('className:', generateBtn.className);
        console.log('计算样式:', window.getComputedStyle(generateBtn));
        console.log('父元素:', generateBtn.parentElement);
        console.log('selectedPhotoFile:', window.selectedPhotoFile);
        
        // 检查是否有覆盖元素
        const rect = generateBtn.getBoundingClientRect();
        const centerX = rect.left + rect.width/2;
        const centerY = rect.top + rect.height/2;
        const elementAtPoint = document.elementFromPoint(centerX, centerY);
        console.log('按钮位置:', `(${centerX}, ${centerY})`);
        console.log('按钮位置的元素:', elementAtPoint);
        console.log('是否被覆盖:', elementAtPoint !== generateBtn);
        
        // 获取所有在该点的元素
        const elementsAtPoint = document.elementsFromPoint(centerX, centerY);
        console.log('该位置的所有元素:', elementsAtPoint);
        
        return generateBtn;
    } else {
        console.error('找不到生成按钮');
        return null;
    }
}

// 生成本地占位图片
function generatePlaceholderImage(text, width = 400, height = 200, bgColor = '#6C5CE7', textColor = '#FFFFFF') {
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    
    // 绘制背景
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, width, height);
    
    // 绘制文字
    ctx.fillStyle = textColor;
    ctx.font = 'bold 24px Arial, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    // 处理长文本换行
    const maxWidth = width - 40;
    const lines = [];
    const words = text.split('');
    let currentLine = '';
    
    for (let i = 0; i < words.length; i++) {
        const testLine = currentLine + words[i];
        const metrics = ctx.measureText(testLine);
        if (metrics.width > maxWidth && currentLine !== '') {
            lines.push(currentLine);
            currentLine = words[i];
        } else {
            currentLine = testLine;
        }
    }
    lines.push(currentLine);
    
    // 绘制多行文字
    const lineHeight = 30;
    const startY = height / 2 - (lines.length - 1) * lineHeight / 2;
    
    lines.forEach((line, index) => {
        ctx.fillText(line, width / 2, startY + index * lineHeight);
    });
    
    return canvas.toDataURL('image/png');
}

// 图片模态框功能
function showImageModal(imageUrl, placeName) {
    if (!imageUrl || imageUrl.includes('placeholder') || imageUrl.includes('via.placeholder')) return;
    
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="image-modal-content">
            <div class="image-modal-header">
                <h3>${placeName}</h3>
                <button class="close-btn" onclick="closeImageModal()">&times;</button>
            </div>
            <img src="${imageUrl}" alt="${placeName}" class="modal-image">
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 添加关闭事件
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeImageModal();
        }
    });
}

function closeImageModal() {
    const modal = document.querySelector('.image-modal');
    if (modal) {
        modal.remove();
    }
}

// 智能提示词生成函数
function generateIntelligentPrompt(place) {
    const name = place.name || '景点';
    const category = place.category || '';
    const description = place.description || '';
    const location = place.city || place.country || '';
    
    // 基础提示词模板
    let prompt = `请将图中的人物与${name}进行完美合影合成。`;
    
    // 根据景点类别添加特定描述
    if (category) {
        const categoryPrompts = {
            '寺庙': '背景是庄严神圣的寺庙建筑，金碧辉煌的佛殿和古典的中式建筑风格',
            '博物馆': '背景是现代化的博物馆建筑，展现文化艺术的氛围',
            '公园': '背景是美丽的自然公园景观，绿树成荫，花草繁茂',
            '古迹': '背景是历史悠久的古代建筑遗迹，展现深厚的历史文化底蕴',
            '山峰': '背景是雄伟壮观的山峰景色，云雾缭绕，气势磅礴',
            '海滩': '背景是碧海蓝天的海滩风光，白沙细软，海浪轻拍',
            '城市地标': '背景是标志性的城市建筑，现代化的都市风光',
            '自然景观': '背景是壮美的自然风光，山川河流，景色宜人',
            '文化景点': '背景是具有文化特色的建筑和环境，体现当地文化特色',
            '购物': '背景是繁华的商业街区或购物中心',
            '娱乐': '背景是充满活力的娱乐场所'
        };
        
        for (const [key, desc] of Object.entries(categoryPrompts)) {
            if (category.includes(key)) {
                prompt += `${desc}，`;
                break;
            }
        }
    }
    
    // 根据描述添加具体细节
    if (description) {
        const keywords = {
            '古老': '古朴典雅的建筑风格',
            '现代': '现代化的建筑设计',
            '宏伟': '气势恢宏的建筑规模',
            '精美': '精美细致的装饰细节',
            '壮观': '令人震撼的壮观景象',
            '美丽': '风景如画的美丽环境',
            '历史': '深厚的历史文化氛围',
            '神圣': '庄严神圣的宗教氛围',
            '自然': '原生态的自然环境',
            '繁华': '繁华热闹的都市景象'
        };
        
        for (const [keyword, enhancement] of Object.entries(keywords)) {
            if (description.includes(keyword)) {
                prompt += `${enhancement}，`;
                break;
            }
        }
    }
    
    // 添加位置信息
    if (location) {
        prompt += `位于${location}，`;
    }
    
    // 添加通用的合影要求
    prompt += '人物穿着适合旅游的休闲装，自然地微笑，天气晴朗。保持人脸的原貌和特征不变，只改变服装和背景。整体画面和谐自然，具有真实的旅游合影效果。';
    
    return prompt;
}

// 景点合影生成功能
function openSelfieGenerator(placeIndex, attractionName, location) {
    // 从全局场景数据中获取完整的景点信息
    let place = null;
    
    // 首先尝试通过索引获取
    if (placeIndex >= 0 && placeIndex < sceneManagement.allScenes.length) {
        place = sceneManagement.allScenes[placeIndex];
    }
    
    // 如果索引无效，尝试通过名称查找
    if (!place && attractionName) {
        place = sceneManagement.allScenes.find(p => p.name === attractionName);
        if (place) {
            logger.info(`通过名称找到景点: ${attractionName}`);
        }
    }
    
    // 如果仍然找不到，创建一个基本的景点对象
    if (!place) {
        logger.warning(`无法找到景点信息，使用基本信息: ${attractionName}`);
        place = {
            name: attractionName || '未知景点',
            city: location || '',
            country: location || '',
            latitude: null,
            longitude: null
        };
    }
    
    const finalAttractionName = place.name || attractionName;
    const finalLocation = place.city || place.country || location || '';
    
    logger.info(`打开合影生成器 - 景点: ${finalAttractionName}, 位置: ${finalLocation}`);
    
    // 保存当前景点信息到全局变量
    window.currentAttractionInfo = {
        name: finalAttractionName,
        location: finalLocation,
        index: placeIndex,
        ...place
    };
    
    // 显示合影模态框
    const modal = document.getElementById('selfieModal');
    const overlay = document.getElementById('selfieOverlay');
    
    if (modal && overlay) {
        // 更新模态框内容
        const attractionNameEl = document.getElementById('selfieAttractionName');
        const attractionLocationEl = document.getElementById('selfieAttractionLocation');
        
        if (attractionNameEl) attractionNameEl.textContent = finalAttractionName;
        if (attractionLocationEl) attractionLocationEl.textContent = finalLocation;
    
    // 显示模态框
        modal.style.display = 'block';
        overlay.style.display = 'block';
        
        // 重置状态
        resetSelfieGenerator();
        
        logger.info('✅ 合影生成器已打开');
                } else {
        logger.error('❌ 找不到合影模态框元素');
        alert('界面加载错误，请刷新页面重试');
    }
}

function closeSelfieGenerator() {
    // 这个函数已经被 closeSelfieModal 替代，保留兼容性
    closeSelfieModal();
}

function setupPhotoUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const photoInput = document.getElementById('photoInput');
    const styleUploadArea = document.getElementById('styleUploadArea');
    const styleInput = document.getElementById('styleInput');
    const generateBtn = document.getElementById('attractionGenerateBtn');
    
    logger.info('📋 setupPhotoUpload 被调用');
    
    // 设置个人照片上传
    if (uploadArea && photoInput) {
        // 移除旧的事件监听器（如果存在）
        const newUploadArea = uploadArea.cloneNode(true);
        uploadArea.parentNode.replaceChild(newUploadArea, uploadArea);
        
        // 拖拽上传 - 个人照片
        setupDragAndDrop('uploadArea', (file) => handlePhotoSelect(file));
        
        // 文件选择事件 - 个人照片
        const newPhotoInput = document.getElementById('photoInput');
        if (newPhotoInput) {
            newPhotoInput.onchange = function(e) {
                if (this.files && this.files.length > 0) {
                    logger.info('📁 个人照片文件输入change事件触发');
                    handlePhotoSelect(this.files[0]);
                }
            };
        }
    }
    
    // 设置范例照片上传
    if (styleUploadArea && styleInput) {
        // 拖拽上传 - 范例照片
        setupDragAndDrop('styleUploadArea', (file) => handleStylePhotoSelect(file));
        
        // 文件选择事件 - 范例照片
        const newStyleInput = document.getElementById('styleInput');
        if (newStyleInput) {
            newStyleInput.onchange = function(e) {
                if (this.files && this.files.length > 0) {
                    logger.info('🎨 范例照片文件输入change事件触发');
                    handleStylePhotoSelect(this.files[0]);
                }
            };
        }
    }
    
    logger.info('✅ setupPhotoUpload 完成');
}

// 防止重复处理
let isProcessingPhoto = false;

// 全局函数：处理照片选择
window.handlePhotoSelect = function(file) {
    logger.info(`📸 handlePhotoSelect 被调用, file: ${file ? file.name : 'null'}`);
    
    // 防止重复处理
    if (isProcessingPhoto) {
        logger.warning('⚠️ 正在处理照片，忽略重复调用');
        return;
    }
    
    // 检查文件是否存在
    if (!file) {
        logger.warning('没有选择文件');
        return;
    }
    
    isProcessingPhoto = true;
    
    // 验证文件类型
    if (!file.type.startsWith('image/')) {
        alert('请选择有效的图片文件');
        return;
    }
    
    // 验证文件大小（限制为10MB）
    if (file.size > 10 * 1024 * 1024) {
        alert('图片文件过大，请选择小于10MB的图片');
        isProcessingPhoto = false;
        return;
    }
    
    logger.info(`📂 文件验证通过: ${file.name}, 大小: ${(file.size / 1024 / 1024).toFixed(2)}MB`);
    
    // 读取并预览图片
    const reader = new FileReader();
    reader.onload = (e) => {
        // 尝试获取不同的预览元素（兼容新旧版本）
        const previewImage = document.getElementById('previewImage') || document.getElementById('uploadPreview');
        const uploadArea = document.getElementById('uploadArea');
        const photoPreview = document.getElementById('photoPreview');
        const generateBtn = document.getElementById('attractionGenerateBtn') || document.getElementById('generateBtn');
        const uploadPlaceholder = document.getElementById('uploadPlaceholder');
        
        if (previewImage) {
            previewImage.src = e.target.result;
            previewImage.style.display = 'block';
        }
        
        // 隐藏上传占位符，显示预览
        if (uploadPlaceholder) {
            uploadPlaceholder.style.display = 'none';
        }
        
        if (photoPreview) {
            uploadArea.style.display = 'none';
            photoPreview.style.display = 'block';
        }
        
        // 启用生成按钮
        forceEnableGenerateButton();
        
        // 存储文件以供后续使用
        window.selectedPhotoFile = file;
        
        logger.success(`照片已选择: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`);
    };
    
    reader.readAsDataURL(file);
    
    // 处理完成后重置标志
    setTimeout(() => {
        isProcessingPhoto = false;
    }, 100);
};

// 处理HTML中的照片上传（兼容旧版本）
function handlePhotoUpload(event) {
    const file = event.target.files[0];
    if (file) {
        handlePhotoSelect(file);
    }
}

// 处理范例风格图片上传
function handleStylePhotoUpload(event) {
    const file = event.target.files[0];
    if (file) {
        handleStylePhotoSelect(file);
    }
}

// 处理范例风格图片选择
function handleStylePhotoSelect(file) {
    logger.info(`📸 选择范例风格图片: ${file.name}, 大小: ${(file.size / 1024 / 1024).toFixed(2)}MB`);
    
    // 验证文件类型
    if (!file.type.startsWith('image/')) {
        alert('请选择有效的图片文件');
        return;
    }
    
    // 验证文件大小（限制为10MB）
    if (file.size > 10 * 1024 * 1024) {
        alert('图片文件过大，请选择小于10MB的图片');
        return;
    }
    
    // 保存文件到全局变量
        window.selectedStyleFile = file;
        
    // 显示预览
    const reader = new FileReader();
    reader.onload = function(e) {
        const stylePreview = document.getElementById('stylePreview');
        const stylePlaceholder = document.getElementById('stylePlaceholder');
        
        if (stylePreview && stylePlaceholder) {
            stylePreview.src = e.target.result;
            stylePreview.style.display = 'block';
            stylePlaceholder.style.display = 'none';
            
            logger.info('✅ 范例风格图片预览已显示');
            
            // 更新提示词占位符
            const customPrompt = document.getElementById('customPrompt');
            if (customPrompt && !customPrompt.value.trim()) {
                customPrompt.placeholder = '已上传范例风格图片，输入额外要求将追加到风格迁移提示词后面。例如：按第二个橙色高子男生，换他的衣服和裤子服装，头像更换成当前主人的头像，只保留一个人';
            }
        }
    };
    reader.readAsDataURL(file);
}

// 全局函数：生成景点合影照片
window.generateAttractionPhoto = async function(attractionName, location, placeIndex) {
    logger.info(`🎨 generateAttractionPhoto 被调用: ${attractionName}, ${location}, ${placeIndex}`);
    logger.info(`📷 selectedPhotoFile: ${window.selectedPhotoFile ? window.selectedPhotoFile.name : 'null'}`);
    
    if (!window.selectedPhotoFile) {
        alert('请先选择照片');
        logger.error('❌ 没有选择照片文件');
        return;
    }
    
    // 获取完整的景点信息
    let place = window.currentAttractionInfo;
    
    // 如果没有当前景点信息，尝试从场景管理中获取
    if (!place && placeIndex >= 0 && placeIndex < sceneManagement.allScenes.length) {
        place = sceneManagement.allScenes[placeIndex];
    }
    
    // 如果仍然没有，使用基本信息
    if (!place) {
        place = {
            name: document.getElementById('attractionName')?.textContent || '未知景点',
            city: document.getElementById('locationInfo')?.textContent || '',
            country: '',
            latitude: null,
            longitude: null
        };
        logger.warning('使用基本景点信息生成合影');
    }
    
    const generateBtn = document.getElementById('attractionGenerateBtn') || document.getElementById('generateBtn');
    const loadingIndicator = document.getElementById('loadingIndicator') || document.getElementById('selfieLoading');
    const customPrompt = document.getElementById('customPrompt');
    const customPromptValue = customPrompt ? customPrompt.value.trim() : '';
    
    logger.info(`🔧 元素状态: generateBtn=${generateBtn ? '存在' : '不存在'}, loadingIndicator=${loadingIndicator ? '存在' : '不存在'}`);
    
    try {
        // 显示加载状态
        if (generateBtn) generateBtn.disabled = true;
        if (loadingIndicator) loadingIndicator.style.display = 'block';
        
        logger.info(`开始生成${place.name}合影照片...`);
        
        // 创建包含完整景点信息的FormData
        const formData = new FormData();
        formData.append('user_photo', window.selectedPhotoFile);
        formData.append('attraction_name', place.name);
        
        // 如果有范例照片，添加到FormData
        if (window.selectedStyleFile) {
            formData.append('style_photo', window.selectedStyleFile);
            logger.info(`📎 添加范例照片: ${window.selectedStyleFile.name}`);
        }
        
        // 传递完整的景点信息
        if (place.city) formData.append('location', place.city);
        if (place.category) formData.append('category', place.category);
        if (place.description) formData.append('description', place.description);
        if (place.opening_hours) formData.append('opening_hours', place.opening_hours);
        if (place.ticket_price) formData.append('ticket_price', place.ticket_price);
        if (place.latitude) formData.append('latitude', place.latitude.toString());
        if (place.longitude) formData.append('longitude', place.longitude.toString());
        if (customPromptValue) formData.append('custom_prompt', customPromptValue);
        
        // 调用后端API
        const response = await fetch(`${API_BASE_URL}/api/generate-attraction-photo`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '生成失败');
        }
        
        const result = await response.json();
        
        if (result.success) {
            // 显示生成结果
            logger.info('📊 后端返回数据:', result.data);
            showGeneratedPhoto(result.data);
            logger.success(`✅ ${attractionName}合影照片生成成功！`);
        } else {
            throw new Error(result.message || '生成失败');
        }
        
    } catch (error) {
        logger.error(`❌ 生成合影照片失败: ${error.message}`);
        alert(`生成失败: ${error.message}`);
    } finally {
        // 恢复按钮状态
        if (generateBtn) generateBtn.disabled = false;
        if (loadingIndicator) loadingIndicator.style.display = 'none';
    }
};

// 显示生成的照片
function showGeneratedPhoto(data) {
    // 隐藏上传区域
    const selfieUploadSection = document.getElementById('selfieUploadSection');
    const selfieLoading = document.getElementById('selfieLoading');
    const selfieResult = document.getElementById('selfieResult');
    const generatedSelfie = document.getElementById('generatedSelfie');
    
    // 保持上传区域可见，只隐藏加载状态
    // if (selfieUploadSection) selfieUploadSection.style.display = 'none';  // 注释掉，保持上传区域可见
    if (selfieLoading) selfieLoading.style.display = 'none';
    
    // 显示结果
    if (selfieResult && generatedSelfie) {
        generatedSelfie.src = data.image_url || data.base64;
        selfieResult.style.display = 'block';
        
        // 保存生成的照片数据
        window.generatedPhotoData = data;
        
        logger.info('✅ 生成的照片已显示');
        logger.info('📊 保存的照片数据:', {
            hasBase64: !!data.base64,
            hasImageUrl: !!data.image_url,
            filename: data.filename,
            attraction: data.attraction
        });
    }
    
    // 更新生成按钮文字，提示可以重新生成
    const generateBtn = document.getElementById('attractionGenerateBtn') || document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.innerHTML = '✨ 重新生成合影';
        generateBtn.disabled = false;
    }
}

// 下载生成的照片
function downloadSelfie() {
    if (window.generatedPhotoData) {
        // 获取图片URL，优先使用base64，其次使用image_url
        const imageUrl = window.generatedPhotoData.base64 || window.generatedPhotoData.image_url;
        
        if (!imageUrl) {
            logger.error('❌ 没有可下载的图片数据');
            alert('图片数据不可用，无法下载');
            return;
        }
        
        const link = document.createElement('a');
        link.href = imageUrl;
        link.download = window.generatedPhotoData.filename || 'attraction_selfie.png';
        document.body.appendChild(link); // 添加到DOM中
        link.click();
        document.body.removeChild(link); // 下载后移除
        
        logger.info('📥 照片下载已触发');
        logger.info(`📎 下载文件名: ${link.download}`);
    } else {
        logger.error('❌ 没有生成的照片可供下载');
        alert('请先生成照片');
    }
}

// 分享照片
function shareSelfie() {
    if (navigator.share && window.generatedPhotoData) {
        navigator.share({
            title: '我的景点合影',
            text: '看看我在' + (window.generatedPhotoData.attraction || '景点') + '的合影！',
            url: window.location.href
        }).catch(console.error);
    } else {
        // 复制到剪贴板作为备选方案
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert('链接已复制到剪贴板');
        });
    }
}

// 重置合影生成器
function resetSelfieGenerator() {
    // 重置用户照片
    const uploadPreview = document.getElementById('uploadPreview');
    const uploadPlaceholder = document.getElementById('uploadPlaceholder');
    if (uploadPreview && uploadPlaceholder) {
        uploadPreview.style.display = 'none';
        uploadPlaceholder.style.display = 'block';
    }
    
    // 重置范例风格图片
    const stylePreview = document.getElementById('stylePreview');
    const stylePlaceholder = document.getElementById('stylePlaceholder');
    if (stylePreview && stylePlaceholder) {
        stylePreview.style.display = 'none';
        stylePlaceholder.style.display = 'block';
    }
    
    // 重置文件选择
    const selfiePhotoInput = document.getElementById('selfiePhotoInput');
    const stylePhotoInput = document.getElementById('stylePhotoInput');
    if (selfiePhotoInput) selfiePhotoInput.value = '';
    if (stylePhotoInput) stylePhotoInput.value = '';
    
    // 清除全局变量
    window.selectedPhotoFile = null;
    window.selectedStyleFile = null;
    
    // 重置提示词
    const customPrompt = document.getElementById('customPrompt');
    if (customPrompt) {
        customPrompt.value = '';
        customPrompt.placeholder = '输入额外要求，将追加到基础提示词后面。例如：按第二个橙色高子男生，换他的衣服和裤子服装，头像更换成当前主人的头像，只保留一个人';
    }
    
    // 隐藏结果和错误
    const selfieResult = document.getElementById('selfieResult');
    const selfieError = document.getElementById('selfieError');
    const selfieLoading = document.getElementById('selfieLoading');
    const selfieUploadSection = document.getElementById('selfieUploadSection');
    
    if (selfieResult) selfieResult.style.display = 'none';
    if (selfieError) selfieError.style.display = 'none';
    if (selfieLoading) selfieLoading.style.display = 'none';
    if (selfieUploadSection) selfieUploadSection.style.display = 'block';
    
    // 重新启用生成按钮
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.disabled = true; // 需要重新选择照片才能启用
    }
}

// 关闭合影模态框
function closeSelfieModal() {
    const modal = document.getElementById('selfieModal');
    const overlay = document.getElementById('selfieOverlay');
    
    if (modal) modal.style.display = 'none';
    if (overlay) overlay.style.display = 'none';
    
    // 重置状态
    resetSelfieGenerator();
}

// 当前风格重新生成（保留已上传的图片）
function regenerateWithCurrentStyle() {
    // 检查是否有必要的文件
    if (!window.selectedPhotoFile) {
        logger.error('❌ 没有用户照片，无法重新生成');
        alert('请先上传用户照片');
        return;
    }
    
    // 隐藏当前结果，准备重新生成
    const selfieResult = document.getElementById('selfieResult');
    if (selfieResult) {
        selfieResult.style.display = 'none';
    }
    
    logger.info('🔄 使用当前风格重新生成合影');
    
    // 调用生成函数
    generateSelfie();
}

// 自动滑动到生成等待界面
function scrollToGenerationLoading() {
    // 延迟执行滚动，确保loading元素已显示
    setTimeout(() => {
        // 查找生成等待界面的元素
        const loadingElement = document.getElementById('selfieLoading');
        
        if (loadingElement) {
            // 先显示loading元素
            loadingElement.style.display = 'block';
            
            // 平滑滚动到等待界面
            loadingElement.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center',
                inline: 'nearest'
            });
            logger.info('🎯 自动滑动到生成等待界面');
        } else {
            // 如果找不到等待界面，尝试滚动到模态框的loading区域
            const modal = document.getElementById('selfieModal');
            if (modal && modal.style.display !== 'none') {
                // 查找模态框内的滚动容器
                const modalBody = modal.querySelector('.selfie-body');
                if (modalBody) {
                    // 滚动到模态框body的底部（loading通常在底部）
                    modalBody.scrollTop = modalBody.scrollHeight - modalBody.clientHeight;
                    logger.info('🎯 滑动到模态框loading区域');
                }
            }
        }
    }, 100);
}

// 合影生成函数
function generateSelfie() {
    logger.info('🎨 开始生成合影');
    
    // 检查是否有当前景点信息
    if (!window.currentAttractionInfo) {
        logger.error('❌ 没有当前景点信息');
        alert('景点信息获取失败，请重新打开合影生成器');
        return;
    }
    
    // 检查是否选择了照片
    if (!window.selectedPhotoFile) {
        logger.error('❌ 没有选择用户照片');
        alert('请先选择您的照片');
        return;
    }
    
    // 🎯 自动滑动到生成等待界面
    scrollToGenerationLoading();
    
    const { name, location, index } = window.currentAttractionInfo;
    logger.info(`📸 ${t('generatePhoto')} - 景点: ${name}, 位置: ${location}, 索引: ${index}`);
    
    // 调用生成景点合影照片函数
    window.generateAttractionPhoto(name, location, index);
}

// ==================== 环境配置管理 ====================

// 环境配置管理
window.EnvironmentConfig = {
    // 设置是否使用域名地址
    setUseDomainName: function(useDomain) {
        localStorage.setItem('isUsedomainnameaddress', useDomain.toString());
        logger.info(`🔧 环境配置已更新: 使用域名地址 = ${useDomain}`);
        logger.info('🔄 请刷新页面以应用新配置');
        return useDomain;
    },
    
    // 获取当前配置
    getUseDomainName: function() {
        return localStorage.getItem('isUsedomainnameaddress') === 'true';
    },
    
    // 获取当前API基础URL
    getCurrentAPIBaseURL: function() {
        return API_BASE_URL;
    },
    
    // 切换环境配置
    toggleEnvironment: function() {
        const current = this.getUseDomainName();
        const newValue = !current;
        this.setUseDomainName(newValue);
        
        if (newValue) {
            logger.success('✅ 已切换到生产环境 (https://spot.gitagent.io)');
        } else {
            logger.success('✅ 已切换到本地环境 (http://localhost:8001)');
        }
        
        return newValue;
    },
    
    // 显示当前环境状态
    showStatus: function() {
        const useDomain = this.getUseDomainName();
        const apiUrl = this.getCurrentAPIBaseURL();
        
        logger.info('🔧 当前环境配置:');
        logger.info(`   使用域名地址: ${useDomain}`);
        logger.info(`   API基础URL: ${apiUrl}`);
        logger.info(`   环境类型: ${useDomain ? '生产环境' : '本地环境'}`);
        
        return {
            useDomainName: useDomain,
            apiBaseURL: apiUrl,
            environment: useDomain ? 'production' : 'local'
        };
    }
};

// 暴露新的全局函数
window.playVideo = playVideo;
window.closeVideoModal = closeVideoModal;
window.showImageModal = showImageModal;
window.closeImageModal = closeImageModal;
window.openSelfieGenerator = openSelfieGenerator;
window.closeSelfieGenerator = closeSelfieGenerator;
window.generateSelfie = generateSelfie;
window.handlePhotoUpload = handlePhotoUpload;
window.handleStylePhotoUpload = handleStylePhotoUpload;
window.resetSelfieGenerator = resetSelfieGenerator;
window.regenerateWithCurrentStyle = regenerateWithCurrentStyle;
window.closeSelfieModal = closeSelfieModal;
window.scrollToGenerationLoading = scrollToGenerationLoading;

// ==================== Doro合影功能 ====================

// Doro合影全局变量
let doroSelfieData = {
    currentPlaceIndex: null,
    currentStep: 1,
    userPhoto: null,
    selectedDoro: null,
    stylePhoto: null,
    doroList: { preset: [], custom: [] },
    generatedImage: null
};

// 打开Doro合影模态框
function openDoroSelfie(placeIndex, attractionName, category, location) {
    let place = null;
    
    // 首先尝试通过索引获取
    if (placeIndex >= 0 && placeIndex < sceneManagement.allScenes.length) {
        place = sceneManagement.allScenes[placeIndex];
    }
    
    // 如果索引无效，尝试通过名称查找
    if (!place && attractionName) {
        place = sceneManagement.allScenes.find(p => p.name === attractionName);
        if (place) {
            logger.info(`通过名称找到景点: ${attractionName}`);
        }
    }
    
    // 如果仍然找不到，创建一个基本的景点对象
    if (!place) {
        logger.warning(`无法找到景点信息，使用基本信息: ${attractionName}`);
        place = {
            name: attractionName || '未知景点',
            city: location || '',
            country: location || '',
            category: category || '',
            latitude: null,
            longitude: null
        };
    }
    
    // 保存当前景点信息
    doroSelfieData.currentPlaceIndex = placeIndex;
    doroSelfieData.currentPlace = place;
    
    // 更新景点信息显示
    document.getElementById('doroAttractionName').textContent = place.name || attractionName;
    document.getElementById('doroAttractionLocation').textContent = 
        place.city || place.country || location || '未知位置';
    
    // 重置状态
    resetDoroGenerator();
    
    // 加载Doro列表
    loadDoroList();
    
    // 显示模态框
    document.getElementById('doroSelfieModal').style.display = 'block';
    document.getElementById('doroOverlay').style.display = 'block';
    
    logger.info(`🤝 打开Doro合影生成器: ${place.name}`);
}

// 关闭Doro模态框
function closeDoroModal() {
    document.getElementById('doroSelfieModal').style.display = 'none';
    document.getElementById('doroOverlay').style.display = 'none';
    resetDoroGenerator();
}

// 重置Doro生成器
function resetDoroGenerator() {
    doroSelfieData = {
        currentPlaceIndex: doroSelfieData.currentPlaceIndex,
        currentStep: 1,
        userPhoto: null,
        selectedDoro: null,
        stylePhoto: null,
        doroList: doroSelfieData.doroList,
        generatedImage: null
    };
    
    // 清空预览
    const userPhotoPreview = document.getElementById('userPhotoPreview');
    const userPhotoPlaceholder = document.getElementById('userPhotoPlaceholder');
    const doroStylePreview = document.getElementById('doroStylePreview');
    
    if (userPhotoPreview) userPhotoPreview.style.display = 'none';
    if (userPhotoPlaceholder) userPhotoPlaceholder.style.display = 'block';
    if (doroStylePreview) doroStylePreview.style.display = 'none';
    
    // 重置选项
    const customPrompt = document.getElementById('doroCustomPrompt');
    if (customPrompt) customPrompt.value = '';
    
    // 隐藏结果和错误
    const doroResult = document.getElementById('doroResult');
    const doroError = document.getElementById('doroError');
    const doroLoading = document.getElementById('doroLoading');
    
    if (doroResult) doroResult.style.display = 'none';
    if (doroError) doroError.style.display = 'none';
    if (doroLoading) doroLoading.style.display = 'none';
    
    // 更新生成按钮状态
    updateGenerateButton();
}

// 加载Doro列表
async function loadDoroList() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/doro/list`);
        if (!response.ok) throw new Error('Failed to load Doro list');
        
        const data = await response.json();
        if (data.success) {
            doroSelfieData.doroList = data.data;
            renderDoroSelector('preset');
            logger.info(`✅ 加载Doro列表成功: ${data.data.preset.length}个预设, ${data.data.custom.length}个自定义`);
        }
    } catch (error) {
        logger.error('❌ 加载Doro列表失败:', error);
        // 使用默认Doro
        renderDefaultDoros();
    }
}

// 渲染Doro选择器
function renderDoroSelector(tab) {
    const grid = document.getElementById('doroSelectorGrid');
    grid.innerHTML = '';
    
    const doros = tab === 'preset' ? doroSelfieData.doroList.preset : doroSelfieData.doroList.custom;
    
    if (doros.length === 0 && tab === 'preset') {
        // 如果没有预设Doro，创建默认的
        renderDefaultDoros();
        return;
    }
    
    if (doros.length === 0 && tab === 'custom') {
        grid.innerHTML = '<p class="no-doros">暂无自定义Doro，请上传</p>';
        return;
    }
    
    doros.forEach(doro => {
        const doroItem = document.createElement('div');
        doroItem.className = 'doro-item';
        doroItem.dataset.doroId = doro.id;
        doroItem.innerHTML = `
            <img src="${doro.url || doro.thumbnail}" alt="${doro.name}">
            <div class="doro-item-name">${doro.name}</div>
        `;
        doroItem.onclick = () => selectDoro(doro);
        
        if (doroSelfieData.selectedDoro && doroSelfieData.selectedDoro.id === doro.id) {
            doroItem.classList.add('selected');
        }
        
        grid.appendChild(doroItem);
    });
}

// 渲染默认Doro（当API不可用时）
function renderDefaultDoros() {
    const defaultDoros = [
        { id: 'doro1', name: '经典Doro', url: `${API_BASE_URL}/api/doro/image/doro1` },
        { id: 'doro2', name: '冒险Doro', url: `${API_BASE_URL}/api/doro/image/doro2` },
        { id: 'doro3', name: '时尚Doro', url: `${API_BASE_URL}/api/doro/image/doro3` },
        { id: 'doro4', name: '学者Doro', url: `${API_BASE_URL}/api/doro/image/doro4` },
        { id: 'doro5', name: '运动Doro', url: `${API_BASE_URL}/api/doro/image/doro5` },
        { id: 'doro6', name: '艺术Doro', url: `${API_BASE_URL}/api/doro/image/doro6` },
        { id: 'doro7', name: '商务Doro', url: `${API_BASE_URL}/api/doro/image/doro7` },
        { id: 'doro8', name: '休闲Doro', url: `${API_BASE_URL}/api/doro/image/doro8` },
        { id: 'doro9', name: '节日Doro', url: `${API_BASE_URL}/api/doro/image/doro9` },
        { id: 'doro10', name: '神秘Doro', url: `${API_BASE_URL}/api/doro/image/doro10` },
        { id: 'doro11', name: '温暖Doro', url: `${API_BASE_URL}/api/doro/image/doro11` },
        { id: 'doro12', name: '科技Doro', url: `${API_BASE_URL}/api/doro/image/doro12` },
        { id: 'doro13', name: '自然Doro', url: `${API_BASE_URL}/api/doro/image/doro13` },
        { id: 'doro14', name: '梦幻Doro', url: `${API_BASE_URL}/api/doro/image/doro14` }
    ];
    
    doroSelfieData.doroList.preset = defaultDoros;
    renderDoroSelector('preset');
}

// 选择Doro
function selectDoro(doro) {
    doroSelfieData.selectedDoro = doro;
    
    // 更新选中状态
    document.querySelectorAll('.doro-item').forEach(item => {
        item.classList.remove('selected');
    });
    document.querySelector(`.doro-item[data-doro-id="${doro.id}"]`)?.classList.add('selected');
    
    // 更新生成按钮状态
    updateGenerateButton();
    
    logger.info(`✅ 选择Doro: ${doro.name}`);
}

// 切换Doro标签页
function switchDoroTab(tab) {
    // 更新标签状态
    document.querySelectorAll('.doro-tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    
    // 显示/隐藏内容
    if (tab === 'preset') {
        document.getElementById('doroSelectorGrid').style.display = 'grid';
        document.getElementById('doroUploadCustom').style.display = 'none';
        renderDoroSelector('preset');
    } else {
        document.getElementById('doroSelectorGrid').style.display = 'grid';
        document.getElementById('doroUploadCustom').style.display = 'block';
        renderDoroSelector('custom');
    }
}

// 处理用户照片上传
function handleDoroUserPhoto(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // 验证文件类型
    if (!file.type.startsWith('image/')) {
        alert('请上传图片文件');
        return;
    }
    
    // 验证文件大小（最大10MB）
    if (file.size > 10 * 1024 * 1024) {
        alert('图片大小不能超过10MB');
        return;
    }
    
    doroSelfieData.userPhoto = file;
    
    // 显示预览
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('userPhotoPreview').src = e.target.result;
        document.getElementById('userPhotoPreview').style.display = 'block';
        document.getElementById('userPhotoPlaceholder').style.display = 'none';
        updateGenerateButton();
    };
    reader.readAsDataURL(file);
    
    logger.info(`✅ 上传用户照片: ${file.name}`);
}

// 处理自定义Doro上传
async function handleCustomDoro(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // 验证文件
    if (!file.type.startsWith('image/')) {
        alert('请上传图片文件');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        alert('图片大小不能超过10MB');
        return;
    }
    
    try {
        // 上传到服务器
        const formData = new FormData();
        formData.append('file', file);
        formData.append('name', `自定义Doro_${Date.now()}`);
        
        const response = await fetch(`${API_BASE_URL}/api/doro/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) throw new Error('Upload failed');
        
        const data = await response.json();
        if (data.success) {
            // 添加到自定义列表
            doroSelfieData.doroList.custom.push(data.data);
            
            // 切换到自定义标签并选中
            switchDoroTab('custom');
            selectDoro(data.data);
            
            logger.info(`✅ 上传自定义Doro成功: ${data.data.name}`);
        }
    } catch (error) {
        logger.error('❌ 上传自定义Doro失败:', error);
        alert('上传失败，请重试');
    }
}

// 处理服装风格照片上传
function handleDoroStylePhoto(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // 验证文件
    if (!file.type.startsWith('image/')) {
        alert('请上传图片文件');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) {
        alert('图片大小不能超过10MB');
        return;
    }
    
    doroSelfieData.stylePhoto = file;
    
    // 显示预览
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('doroStylePreview').src = e.target.result;
        document.getElementById('doroStylePreview').style.display = 'block';
        document.getElementById('stylePlaceholder').style.display = 'none';
        updateDoroPreview();
    };
    reader.readAsDataURL(file);
    
    logger.info(`✅ 上传服装风格参考: ${file.name}`);
}

// 跳过服装风格步骤（新布局中不需要）
function skipStyleStep() {
    doroSelfieData.stylePhoto = null;
    const doroStylePreview = document.getElementById('doroStylePreview');
    const stylePlaceholder = document.getElementById('stylePlaceholder');
    
    if (doroStylePreview) doroStylePreview.style.display = 'none';
    if (stylePlaceholder) stylePlaceholder.style.display = 'block';
    
    updateGenerateButton();
}

// 更新Doro预览（简化版本，因为新布局不需要预览区域）
function updateDoroPreview() {
    // 新布局中不需要预览区域，直接更新生成按钮状态
    updateGenerateButton();
}

// 显示Doro选项（新布局中不需要此功能）
function showDoroOptions() {
    // 新布局中所有选项都在界面上可见，不需要动态显示
}

// 更新步骤（新布局中不需要步骤管理）
function updateDoroStep(step) {
    doroSelfieData.currentStep = step;
    // 新布局中所有功能都在一个界面中，不需要步骤管理
    updateGenerateButton();
}

// 下一步（新布局中不需要）
function nextDoroStep() {
    // 新布局中不需要步骤导航
}

// 上一步（新布局中不需要）
function previousDoroStep() {
    // 新布局中不需要步骤导航
}

// 更新生成按钮状态
function updateGenerateButton() {
    const generateBtn = document.getElementById('doroGenerateBtn');
    const videoBtn = document.getElementById('doroVideoBtn');
    
    if (generateBtn) {
        const canGenerate = doroSelfieData.userPhoto && doroSelfieData.selectedDoro;
        generateBtn.disabled = !canGenerate;
        
        if (canGenerate) {
            generateBtn.style.opacity = '1';
            generateBtn.style.cursor = 'pointer';
        } else {
            generateBtn.style.opacity = '0.6';
            generateBtn.style.cursor = 'not-allowed';
        }
    }
    
    // 同步更新视频生成按钮状态
    if (videoBtn) {
        const canGenerate = doroSelfieData.userPhoto && doroSelfieData.selectedDoro;
        videoBtn.disabled = !canGenerate;
        
        if (canGenerate) {
            videoBtn.style.opacity = '1';
            videoBtn.style.cursor = 'pointer';
        } else {
            videoBtn.style.opacity = '0.6';
            videoBtn.style.cursor = 'not-allowed';
        }
    }
}

// 自动滑动到Doro生成等待界面
function scrollToDoroGenerationLoading() {
    // 延迟执行滚动，确保loading元素已显示
    setTimeout(() => {
        // 查找Doro生成等待界面的元素
        const loadingElement = document.getElementById('doroLoading');
        
        if (loadingElement) {
            // 先显示loading元素
            loadingElement.style.display = 'block';
            
            // 平滑滚动到等待界面
            loadingElement.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center',
                inline: 'nearest'
            });
            logger.info('🎯 自动滑动到Doro生成等待界面');
        } else {
            // 如果找不到等待界面，尝试滚动到模态框的loading区域
            const modal = document.getElementById('doroSelfieModal');
            if (modal && modal.style.display !== 'none') {
                // 查找模态框内的滚动容器
                const modalBody = modal.querySelector('.doro-body');
                if (modalBody) {
                    // 滚动到模态框body的底部（loading通常在底部）
                    modalBody.scrollTop = modalBody.scrollHeight - modalBody.clientHeight;
                    logger.info('🎯 滑动到Doro模态框loading区域');
                }
            }
        }
    }, 100);
}

// 生成Doro合影
async function generateDoroSelfie() {
    if (!doroSelfieData.userPhoto || !doroSelfieData.selectedDoro) {
        alert('请完成所有必要步骤');
        return;
    }
    
    // 🎯 自动滑动到Doro生成等待界面
    scrollToDoroGenerationLoading();
    
    let place = null;
    
    // 尝试获取景点信息
    if (doroSelfieData.currentPlaceIndex >= 0 && doroSelfieData.currentPlaceIndex < sceneManagement.allScenes.length) {
        place = sceneManagement.allScenes[doroSelfieData.currentPlaceIndex];
    }
    
    // 如果没有找到，使用存储的景点信息或基本信息
    if (!place) {
        place = doroSelfieData.currentPlace || {
            name: document.querySelector('#doroAttractionName')?.textContent || '未知景点',
            city: document.querySelector('#doroLocationInfo')?.textContent || '',
            country: '',
            category: '',
            latitude: null,
            longitude: null
        };
        logger.warning('使用备用景点信息生成Doro合影');
    }
    
    // 显示加载状态
    document.getElementById('doroLoading').style.display = 'block';
    
    // 滚动到加载区域
    setTimeout(() => {
        const loadingElement = document.getElementById('doroLoading');
        if (loadingElement) {
            loadingElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
    
    try {
        // 准备表单数据
        const formData = new FormData();
        formData.append('user_photo', doroSelfieData.userPhoto);
        
        // 添加Doro（ID或文件）
        if (doroSelfieData.selectedDoro.type === 'preset') {
            formData.append('doro_id', doroSelfieData.selectedDoro.id);
        } else {
            // 自定义Doro，使用ID
            formData.append('doro_id', `custom_${doroSelfieData.selectedDoro.id}`);
        }
        
        // 添加服装风格（如果有）
        if (doroSelfieData.stylePhoto) {
            formData.append('style_photo', doroSelfieData.stylePhoto);
        }
        
        // 添加景点信息
        formData.append('attraction_name', place.name);
        formData.append('attraction_type', place.category || '');
        formData.append('location', place.city || place.country || '');
        
        // 添加自定义提示词
        const customPrompt = document.getElementById('doroCustomPrompt').value;
        if (customPrompt) {
            formData.append('user_description', customPrompt);
        }
        
        logger.info(`🎨 开始生成Doro合影: ${place.name}`);
        
        // 调用API
        const response = await fetch(`${API_BASE_URL}/api/doro/generate`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Generation failed');
        }
        
        const data = await response.json();
        
        if (data.success) {
            // 显示结果
            doroSelfieData.generatedImage = data.data;
            document.getElementById('generatedDoroSelfie').src = data.data.image_url;
            
            document.getElementById('doroLoading').style.display = 'none';
            document.getElementById('doroResult').style.display = 'block';
            
            logger.info(`✅ Doro合影生成成功: ${data.data.filename}`);
        } else {
            throw new Error(data.message || '生成失败');
        }
        
    } catch (error) {
        logger.error('❌ 生成Doro合影失败:', error);
        
        document.getElementById('doroLoading').style.display = 'none';
        document.getElementById('doroError').style.display = 'block';
        document.getElementById('doroErrorMessage').textContent = 
            error.message || '生成失败，请重试';
    }
}

// 下载Doro合影
function downloadDoroSelfie() {
    if (!doroSelfieData.generatedImage) return;
    
    const link = document.createElement('a');
    link.href = doroSelfieData.generatedImage.image_url;
    link.download = doroSelfieData.generatedImage.filename || `doro_selfie_${Date.now()}.png`;
    link.click();
    
    logger.info(`💾 下载Doro合影: ${link.download}`);
}

// 重新生成Doro合影
function regenerateDoroSelfie() {
    // 返回到上传界面但保留已选择的内容
    document.getElementById('doroResult').style.display = 'none';
    // 新布局中不需要显示/隐藏上传区域
}

// 分享Doro合影
async function shareDoroSelfie() {
    if (!doroSelfieData.generatedImage) return;
    
    try {
        if (navigator.share) {
            // 先将base64转换为blob
            const response = await fetch(doroSelfieData.generatedImage.image_url);
            const blob = await response.blob();
            const file = new File([blob], 'doro_selfie.png', { type: 'image/png' });
            
            await navigator.share({
                title: 'Doro与我的合影',
                text: `在${doroSelfieData.generatedImage.attraction_name}的精彩合影！`,
                files: [file]
            });
            
            logger.info('✅ 分享Doro合影成功');
        } else {
            // 复制图片链接
            const tempInput = document.createElement('input');
            tempInput.value = window.location.href;
            document.body.appendChild(tempInput);
            tempInput.select();
            document.execCommand('copy');
            document.body.removeChild(tempInput);
            
            alert('链接已复制到剪贴板');
        }
    } catch (error) {
        logger.error('❌ 分享失败:', error);
        alert('分享失败，请重试');
    }
}

// 显示Doro错误信息
function showDoroError(message) {
    // 隐藏加载状态
    document.getElementById('doroLoading').style.display = 'none';
    
    // 隐藏结果区域
    document.getElementById('doroResult').style.display = 'none';
    document.getElementById('doroVideoResult').style.display = 'none';
    
    // 显示错误信息
    document.getElementById('doroError').style.display = 'block';
    document.getElementById('doroErrorMessage').textContent = message || '操作失败，请重试';
    
    // 滚动到错误区域
    setTimeout(() => {
        const errorElement = document.getElementById('doroError');
        if (errorElement) {
            errorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
}

// 重置Doro生成器状态
function resetDoroGenerator() {
    // 隐藏所有状态区域
    document.getElementById('doroLoading').style.display = 'none';
    document.getElementById('doroResult').style.display = 'none';
    document.getElementById('doroVideoResult').style.display = 'none';
    document.getElementById('doroError').style.display = 'none';
}

// ==================== Doro视频生成功能 ====================

// 生成Doro合影视频
async function generateDoroVideo() {
    if (!doroSelfieData.userPhoto || !doroSelfieData.selectedDoro) {
        alert('请完成所有必要步骤');
        return;
    }
    
    // 🎯 自动滑动到Doro生成等待界面（视频和图片共用同一个loading元素）
    scrollToDoroGenerationLoading();
    
    let place = null;
    
    // 尝试获取景点信息
    if (doroSelfieData.currentPlaceIndex >= 0 && doroSelfieData.currentPlaceIndex < sceneManagement.allScenes.length) {
        place = sceneManagement.allScenes[doroSelfieData.currentPlaceIndex];
    }
    
    // 如果没有找到，使用存储的景点信息或基本信息
    if (!place) {
        place = doroSelfieData.currentPlace || {
            name: document.querySelector('#doroAttractionName')?.textContent || '未知景点',
            city: document.querySelector('#doroAttractionLocation')?.textContent || '',
            country: '',
            category: '',
            latitude: null,
            longitude: null,
            description: '美丽的景点'
        };
        logger.info('使用备用景点信息:', place);
    }
    
    // 显示加载状态
    document.getElementById('doroLoading').style.display = 'block';
    
    // 滚动到加载区域
    setTimeout(() => {
        const loadingElement = document.getElementById('doroLoading');
        if (loadingElement) {
            loadingElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
    
    try {
        // 准备表单数据
        const formData = new FormData();
        formData.append('user_photo', doroSelfieData.userPhoto);
        
        // 添加Doro（ID或文件）
        if (doroSelfieData.selectedDoro.type === 'preset') {
            formData.append('doro_id', doroSelfieData.selectedDoro.id);
        } else {
            // 自定义Doro，使用ID
            formData.append('doro_id', `custom_${doroSelfieData.selectedDoro.id}`);
        }
        
        // 添加服装风格（如果有）
        if (doroSelfieData.stylePhoto) {
            formData.append('style_photo', doroSelfieData.stylePhoto);
        }
        
        // 添加景点信息
        formData.append('attraction_name', place.name);
        formData.append('attraction_type', place.category || '');
        formData.append('location', place.city || place.country || '');
        
        // 添加自定义提示词
        const customPrompt = document.getElementById('doroCustomPrompt').value;
        if (customPrompt) {
            formData.append('user_description', customPrompt);
        }
        
        logger.info('🎬 开始生成Doro合影视频...');
        
        // 调用后端API生成视频
        const response = await fetch(`${API_BASE_URL}/api/doro/generate-video`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '视频生成失败');
        }
        
        const data = await response.json();
        
        if (data.success) {
            // 显示结果
            doroSelfieData.generatedVideo = data.data;
            document.getElementById('generatedDoroVideo').src = data.data.video_url;
            
            document.getElementById('doroLoading').style.display = 'none';
            document.getElementById('doroVideoResult').style.display = 'block';
            
            logger.info(`✅ Doro合影视频生成成功: ${data.data.filename}`);
        } else {
            throw new Error(data.message || '视频生成失败');
        }
        
    } catch (error) {
        logger.error('❌ 生成Doro合影视频失败:', error);
        
        document.getElementById('doroLoading').style.display = 'none';
        document.getElementById('doroError').style.display = 'block';
        document.getElementById('doroErrorMessage').textContent = 
            error.message || '视频生成失败，请重试';
    }
}

// 显示Doro视频结果
function displayDoroVideoResult(videoData) {
    // 隐藏其他区域
    document.getElementById('doroResult').style.display = 'none';
    document.getElementById('doroError').style.display = 'none';
    
    // 设置视频源
    const videoElement = document.getElementById('generatedDoroVideo');
    if (videoElement && videoData.video_url) {
        videoElement.src = videoData.video_url;
        videoElement.load(); // 重新加载视频
    }
    
    // 显示视频结果区域
    document.getElementById('doroVideoResult').style.display = 'block';
    
    // 滚动到结果区域
    setTimeout(() => {
        const resultElement = document.getElementById('doroVideoResult');
        if (resultElement) {
            resultElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 100);
}

// 下载Doro合影视频
function downloadDoroVideo() {
    if (!doroSelfieData.generatedVideo) return;
    
    const link = document.createElement('a');
    link.href = doroSelfieData.generatedVideo.video_url;
    link.download = doroSelfieData.generatedVideo.filename || `doro_video_${Date.now()}.mp4`;
    link.click();
    
    logger.info(`💾 下载Doro合影视频: ${link.download}`);
}

// 重新生成Doro合影视频
function regenerateDoroVideo() {
    // 返回到上传界面但保留已选择的内容
    document.getElementById('doroVideoResult').style.display = 'none';
    // 可以再次点击生成视频按钮
}

// 分享Doro合影视频
async function shareDoroVideo() {
    if (!doroSelfieData.generatedVideo) return;
    
    try {
        if (navigator.share) {
            // 先将视频转换为blob
            const response = await fetch(doroSelfieData.generatedVideo.video_url);
            const blob = await response.blob();
            const file = new File([blob], 'doro_video.mp4', { type: 'video/mp4' });
            
            await navigator.share({
                title: 'Doro与我的合影视频',
                text: `在${doroSelfieData.generatedVideo.attraction_name}的精彩合影视频！`,
                files: [file]
            });
            
            logger.info('✅ 分享Doro合影视频成功');
        } else {
            // 复制视频链接
            const tempInput = document.createElement('input');
            tempInput.value = window.location.href;
            document.body.appendChild(tempInput);
            tempInput.select();
            document.execCommand('copy');
            document.body.removeChild(tempInput);
            
            alert('链接已复制到剪贴板');
        }
    } catch (error) {
        logger.error('❌ 视频分享失败:', error);
        alert('分享失败，请重试');
    }
}


// 导出Doro函数到全局
window.openDoroSelfie = openDoroSelfie;
window.closeDoroModal = closeDoroModal;
window.resetDoroGenerator = resetDoroGenerator;
window.showDoroError = showDoroError;
window.switchDoroTab = switchDoroTab;
window.handleDoroUserPhoto = handleDoroUserPhoto;
window.handleCustomDoro = handleCustomDoro;
window.handleDoroStylePhoto = handleDoroStylePhoto;
window.skipStyleStep = skipStyleStep;
window.nextDoroStep = nextDoroStep;
window.previousDoroStep = previousDoroStep;
window.generateDoroSelfie = generateDoroSelfie;
window.generateDoroVideo = generateDoroVideo;
window.downloadDoroSelfie = downloadDoroSelfie;
window.downloadDoroVideo = downloadDoroVideo;
window.regenerateDoroSelfie = regenerateDoroSelfie;
window.regenerateDoroVideo = regenerateDoroVideo;
window.shareDoroSelfie = shareDoroSelfie;
window.shareDoroVideo = shareDoroVideo;
window.downloadSelfie = downloadSelfie;
window.shareSelfie = shareSelfie;
window.scrollToDoroGenerationLoading = scrollToDoroGenerationLoading;

// 版本标识 - 强制浏览器重新加载 - 2025-09-04 01:30 - Doro模态框JavaScript修复版本
