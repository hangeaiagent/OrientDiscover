// 全局变量
let currentPosition = null;
let currentHeading = 0;

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
        const logEntry = {
            timestamp,
            message,
            type,
            id: Date.now()
        };
        
        this.logs.unshift(logEntry);
        if (this.logs.length > this.maxLogs) {
            this.logs.pop();
        }
        
        this.displayLog(logEntry);
        console.log(`[${timestamp}] ${type.toUpperCase()}: ${message}`);
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
    logger.info('🧭 方向探索派对应用启动');
    logger.info('正在初始化应用组件...');
    
    // 检查浏览器支持
    if (!checkBrowserSupport()) {
        const errorMsg = '您的浏览器不支持所需功能，请使用现代浏览器访问';
        logger.error(errorMsg);
        showError(errorMsg);
        return;
    }
    
    logger.success('浏览器兼容性检查通过');
    
    // 请求权限并获取位置
    await requestPermissions();
    
    // 初始化传感器
    initializeCompass();
    
    // 初始化点击指南针功能
    initializeCompassClick();
    
    // 获取初始位置
    refreshLocation();
    
    logger.success('应用初始化完成');
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
        compass.title = '点击设置方向';
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
            <p style="color: #856404; margin: 0 0 10px 0; font-weight: bold;">📍 无法自动获取方向</p>
            <p style="color: #856404; margin: 0 0 10px 0;">请点击指南针设置方向，或手动输入：</p>
            <div style="display: flex; align-items: center; gap: 10px;">
                <input type="number" id="manualHeading" min="0" max="359" value="${currentHeading || 0}" 
                       placeholder="方向角度" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px; width: 120px;">
                <button onclick="setManualHeading()" style="padding: 8px 15px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer;">设置</button>
            </div>
            <p style="font-size: 12px; color: #666; margin: 10px 0 0 0;">💡 提示：0°=北, 90°=东, 180°=南, 270°=西</p>
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
            logger.error('请输入有效的方向角度 (0-359)');
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
            logger.info(`地理位置权限状态: ${geoPermission.state}`);
        }
        
        // 请求设备方向权限 (iOS 13+)
        if (typeof DeviceOrientationEvent.requestPermission === 'function') {
            logger.info('检测到iOS设备，需要请求方向权限');
            try {
            const permission = await DeviceOrientationEvent.requestPermission();
                logger.info(`设备方向权限: ${permission}`);
            if (permission !== 'granted') {
                    logger.warning('需要设备方向权限才能使用指南针功能');
                showError('需要设备方向权限才能使用指南针功能');
                }
            } catch (error) {
                logger.error('设备方向权限请求失败: ' + error.message);
            }
        } else {
            logger.info('设备支持方向检测，无需额外权限');
        }
    } catch (error) {
        logger.error('权限请求失败: ' + error.message);
    }
}

function initializeCompass() {
    logger.info('初始化指南针...');
    
    // 监听设备方向变化
    if (window.DeviceOrientationEvent) {
        logger.info('设备支持方向检测，正在添加事件监听器...');
        
        // 添加deviceorientation事件监听
        window.addEventListener('deviceorientation', function(event) {
            if (event.alpha !== null || event.webkitCompassHeading !== undefined) {
                logger.success('方向事件触发成功');
                handleOrientation(event);
            } else {
                logger.warning('方向事件触发但没有数据');
            }
        }, true);
        
        // 添加deviceorientationabsolute事件监听（某些设备）
        window.addEventListener('deviceorientationabsolute', function(event) {
            if (event.absolute && event.alpha !== null) {
                logger.info('绝对方向事件触发');
                handleOrientation(event);
            }
        }, true);
        
        // 测试是否能获取方向
        setTimeout(() => {
            if (currentHeading === 0) {
                logger.warning('未检测到方向数据，可能需要移动设备或检查权限');
                // 提供手动输入方向的选项
                enableManualHeadingInput();
            }
        }, 1000);  // 缩短到1秒
    } else {
        logger.error('设备不支持方向检测');
        showError('设备不支持方向检测功能');
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
    
    logger.info(`方向更新: ${Math.round(heading)}° (${getDirectionText(heading)})`);
}

function getDirectionText(heading) {
    const directions = [
        { name: '北', min: 0, max: 22.5 },
        { name: '东北', min: 22.5, max: 67.5 },
        { name: '东', min: 67.5, max: 112.5 },
        { name: '东南', min: 112.5, max: 157.5 },
        { name: '南', min: 157.5, max: 202.5 },
        { name: '西南', min: 202.5, max: 247.5 },
        { name: '西', min: 247.5, max: 292.5 },
        { name: '西北', min: 292.5, max: 337.5 },
        { name: '北', min: 337.5, max: 360 }
    ];
    
    for (const dir of directions) {
        if (heading >= dir.min && heading < dir.max) {
            return dir.name;
        }
    }
    return '北';
}

function refreshLocation() {
    logger.info('开始获取位置信息...');
    
    const locationElement = document.getElementById('currentLocation');
    const coordinatesElement = document.getElementById('coordinates');
    const accuracyElement = document.getElementById('accuracy');
    
    locationElement.textContent = '获取中...';
    coordinatesElement.textContent = '获取中...';
    accuracyElement.textContent = '获取中...';
    
    // 检查浏览器支持
    if (!navigator.geolocation) {
        const errorMsg = '❌ 浏览器不支持地理位置功能';
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
    
    if (currentHeading === null || currentHeading === undefined || currentHeading === 0) {
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
        
                // 使用真实数据API端点
        const apiEndpoint = 'http://localhost:8000/api/explore-real';
        logger.info('使用真实数据源');
        
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
    
    card.className = `place-card ${isSelected ? 'selected' : ''} ${isRejected ? 'rejected' : ''}`;
    card.dataset.placeIndex = index;
    
    const modeText = {
        'present': '现代',
        'past': '历史',
        'future': '未来'
    }[settings.timeMode] || '现代';
    
    // 格式化价格显示
    const formatPrice = (price) => {
        if (!price) return '暂无信息';
        if (price.includes('免费')) {
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
            <img src="${place.image || 'https://via.placeholder.com/400x200?text=暂无图片'}" 
                 alt="${place.name}" 
                 class="place-image"
                 onerror="this.src='https://via.placeholder.com/400x200?text=暂无图片'"
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
                <h3 class="place-name">${place.name}</h3>
                <span class="place-distance">${place.distance}km</span>
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
                <button class="action-btn selfie-btn" onclick="openSelfieGenerator(${index})" title="生成景点合影">
                    📸 生成合影
                </button>
                ${place.latitude && place.longitude ? `
                <button class="action-btn streetview-btn" onclick="openStreetView(${place.latitude}, ${place.longitude}, '${place.name.replace(/'/g, "\\'")}')" title="查看街景">
                    🏙️ 查看街景
                </button>
                ` : ''}
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
        
        const response = await fetch('http://localhost:8000/api/journey/start', {
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
        
        const response = await fetch('http://localhost:8000/api/journey/visit', {
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
        
        const response = await fetch(`http://localhost:8000/api/journey/${journeyId}/end`, {
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
        const response = await fetch(`http://localhost:8000/api/journey/${journeyId}`);
        
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
            <img src="${scene.image || 'https://via.placeholder.com/400x200?text=暂无图片'}" 
                 alt="${scene.name}" 
                 class="place-image"
                 onerror="this.src='https://via.placeholder.com/400x200?text=暂无图片'">
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
                <input type="number" id="manualLat" placeholder="例如: 40.0888" step="0.000001" 
                       style="width: 100%; padding: 10px; border: 1px solid #cbd5e0; border-radius: 8px; font-size: 16px;">
            </div>
            <div style="margin-bottom: 20px;">
                <label style="display: block; margin-bottom: 5px; font-weight: bold;">经度 (Longitude):</label>
                <input type="number" id="manualLng" placeholder="例如: 116.3964" step="0.000001" 
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
    document.querySelector('.manual-location-input').remove();
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
        const response = await fetch('http://localhost:8000/api/scene-review', {
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
        const response = await fetch('http://localhost:8000/api/journey-summary', {
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

// 全局暴露街景函数
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

// 漫游功能实现
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

// 地理编码API调用
async function geocodeLocation(query) {
    try {
        const response = await fetch('http://localhost:8000/api/geocode', {
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
        const response = await fetch('http://localhost:8000/api/place-details', {
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
    window.currentPosition = {
        latitude: location.lat,
        longitude: location.lng,
        accuracy: 10 // 高精度
    };
    
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

// 图片模态框功能
function showImageModal(imageUrl, placeName) {
    if (!imageUrl || imageUrl.includes('placeholder')) return;
    
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

// 景点合影生成功能

// 生成基于景点详细信息的智能提示词
function generateIntelligentPrompt(place) {
    const name = place.name || '景点';
    const category = place.category || '';
    const description = place.description || '';
    const location = place.city || place.country || '';
    const openingHours = place.opening_hours || '';
    
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
        // 提取描述中的关键特征
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
                prompt += `展现${enhancement}，`;
                break;
            }
        }
    }
    
    // 根据位置添加地域特色
    if (location) {
        const locationStyles = {
            '北京': '体现中国古都的皇家气派和传统文化',
            '上海': '展现国际化大都市的现代繁华',
            '西安': '彰显古丝绸之路的历史文化底蕴',
            '杭州': '体现江南水乡的诗情画意',
            '成都': '展现巴蜀文化的悠闲惬意',
            '东京': '体现日式文化的精致与现代感',
            '京都': '展现日本传统文化的优雅与禅意',
            '巴黎': '体现法式浪漫与艺术气息',
            '伦敦': '展现英伦风情与历史厚重感',
            '纽约': '体现美式现代都市的活力与自由',
            '罗马': '展现古罗马帝国的历史沧桑',
            '悉尼': '体现澳洲海港城市的现代与自然和谐'
        };
        
        for (const [city, style] of Object.entries(locationStyles)) {
            if (location.includes(city)) {
                prompt += `${style}，`;
                break;
            }
        }
    }
    
    // 添加人物处理要求
    prompt += `人物穿着适合当地文化和气候的得体服装，表情自然愉悦，姿态放松自然。`;
    
    // 添加技术要求
    prompt += `图片要求：高清画质，光线自然，色彩饱和，构图协调。特别重要：保持人物的面部特征、肤色、发型等个人特征完全不变，只改变服装和背景环境。`;
    
    // 添加氛围描述
    const timePrompts = ['阳光明媚的白天', '温暖的午后阳光', '清晨的柔和光线', '黄昏的金色时光'];
    const randomTime = timePrompts[Math.floor(Math.random() * timePrompts.length)];
    prompt += `拍摄时间：${randomTime}，整体氛围温馨愉快，适合纪念留影。`;
    
    return prompt;
}

function openSelfieGenerator(placeIndex) {
    // 从全局场景数据中获取完整的景点信息
    const place = sceneManagement.allScenes[placeIndex];
    if (!place) {
        logger.error(`❌ 找不到索引为 ${placeIndex} 的景点信息`);
        alert('景点信息获取失败，请重试');
        return;
    }
    
    const attractionName = place.name;
    const location = place.city || place.country || '';
    
    logger.info(`打开合影生成器 - 景点: ${attractionName}, 位置: ${location || '未知'}`);
    
    // 生成基于景点详细信息的智能提示词
    const intelligentPrompt = generateIntelligentPrompt(place);
    
    // 创建照片上传模态框
    const modal = document.createElement('div');
    modal.className = 'photo-upload-modal';
    modal.innerHTML = `
        <div class="photo-upload-content">
            <div class="photo-upload-header">
                <h3>📸 生成${attractionName}合影照片</h3>
                <button class="close-btn" onclick="closeSelfieGenerator()">&times;</button>
            </div>
            
            <div class="photo-upload-body">
                <div class="place-info-summary">
                    <div class="place-info-card">
                        <h4>📍 ${attractionName}</h4>
                        ${place.category ? `<p class="info-category">🏷️ ${place.category}</p>` : ''}
                        ${location ? `<p class="info-location">🌍 ${location}</p>` : ''}
                        ${place.description ? `<p class="info-description">${place.description.substring(0, 100)}${place.description.length > 100 ? '...' : ''}</p>` : ''}
                    </div>
                </div>
                
                <div class="upload-section">
                    <div class="upload-area" id="uploadArea">
                        <div class="upload-placeholder">
                            <div class="upload-icon">📷</div>
                            <p>点击或拖拽上传您的照片</p>
                            <p class="upload-hint">支持 JPG, PNG 格式，建议人脸清晰的照片</p>
                        </div>
                        <input type="file" id="photoInput" accept="image/*" style="display: none;">
                    </div>
                    
                    <div class="photo-preview" id="photoPreview" style="display: none;">
                        <img id="previewImage" src="" alt="预览图片">
                        <button class="change-photo-btn" onclick="changePhoto()">更换照片</button>
                    </div>
                </div>
                
                <div class="prompt-section">
                    <label for="customPrompt">AI生成提示词（可编辑）：</label>
                    <textarea id="customPrompt" rows="4">${intelligentPrompt}</textarea>
                    <p class="prompt-hint">💡 提示词已根据景点信息智能生成，您可以根据需要进行修改</p>
                </div>
                
                <div class="generate-section">
                    <button class="generate-btn" id="generateBtn" onclick="generateAttractionPhoto(${placeIndex})" disabled>
                        🎨 生成合影照片
                    </button>
                    <div class="loading-indicator" id="loadingIndicator" style="display: none;">
                        <div class="spinner"></div>
                        <p>正在生成合影照片，请稍候...</p>
                    </div>
                </div>
                
                <div class="result-section" id="resultSection" style="display: none;">
                    <h4>生成结果：</h4>
                    <div class="result-image-container">
                        <img id="resultImage" src="" alt="生成的合影照片">
                        <div class="result-actions">
                            <button class="download-btn" onclick="downloadGeneratedPhoto()">💾 下载照片</button>
                            <button class="regenerate-btn" onclick="regeneratePhoto()">🔄 重新生成</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // 存储当前景点信息供后续使用
    window.currentAttractionInfo = place;
    
    // 设置上传区域事件
    setupPhotoUpload();
    
    // 显示模态框
    setTimeout(() => {
        modal.classList.add('show');
    }, 10);
}

function closeSelfieGenerator() {
    const modal = document.querySelector('.photo-upload-modal');
    if (modal) {
        modal.classList.remove('show');
        setTimeout(() => {
            modal.remove();
        }, 300);
    }
}

function setupPhotoUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const photoInput = document.getElementById('photoInput');
    const photoPreview = document.getElementById('photoPreview');
    const previewImage = document.getElementById('previewImage');
    const generateBtn = document.getElementById('generateBtn');
    
    // 点击上传区域触发文件选择
    uploadArea.addEventListener('click', () => {
        photoInput.click();
    });
    
    // 拖拽上传
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });
    
    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('image/')) {
            handlePhotoSelect(files[0]);
        }
    });
    
    // 文件选择
    photoInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handlePhotoSelect(e.target.files[0]);
        }
    });
}

function handlePhotoSelect(file) {
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
    
    // 读取并预览图片
    const reader = new FileReader();
    reader.onload = (e) => {
        const previewImage = document.getElementById('previewImage');
        const uploadArea = document.getElementById('uploadArea');
        const photoPreview = document.getElementById('photoPreview');
        const generateBtn = document.getElementById('generateBtn');
        
        previewImage.src = e.target.result;
        uploadArea.style.display = 'none';
        photoPreview.style.display = 'block';
        generateBtn.disabled = false;
        
        // 存储文件以供后续使用
        window.selectedPhotoFile = file;
        
        logger.success(`照片已选择: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`);
    };
    
    reader.readAsDataURL(file);
}

function changePhoto() {
    const uploadArea = document.getElementById('uploadArea');
    const photoPreview = document.getElementById('photoPreview');
    const generateBtn = document.getElementById('generateBtn');
    const photoInput = document.getElementById('photoInput');
    
    uploadArea.style.display = 'block';
    photoPreview.style.display = 'none';
    generateBtn.disabled = true;
    photoInput.value = '';
    window.selectedPhotoFile = null;
}

async function generateAttractionPhoto(placeIndex) {
    if (!window.selectedPhotoFile) {
        alert('请先选择照片');
        return;
    }
    
    // 获取完整的景点信息
    const place = window.currentAttractionInfo || sceneManagement.allScenes[placeIndex];
    if (!place) {
        alert('景点信息获取失败，请重试');
        return;
    }
    
    const generateBtn = document.getElementById('generateBtn');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const customPrompt = document.getElementById('customPrompt').value.trim();
    
    try {
        // 显示加载状态
        generateBtn.disabled = true;
        loadingIndicator.style.display = 'block';
        
        logger.info(`开始生成${place.name}合影照片...`);
        
        // 创建包含完整景点信息的FormData
        const formData = new FormData();
        formData.append('user_photo', window.selectedPhotoFile);
        formData.append('attraction_name', place.name);
        
        // 传递完整的景点信息
        if (place.city) formData.append('location', place.city);
        else if (place.country) formData.append('location', place.country);
        
        if (place.category) formData.append('category', place.category);
        if (place.description) formData.append('description', place.description);
        if (place.opening_hours) formData.append('opening_hours', place.opening_hours);
        if (place.ticket_price) formData.append('ticket_price', place.ticket_price);
        
        // 传递坐标信息
        if (place.latitude) formData.append('latitude', place.latitude.toString());
        if (place.longitude) formData.append('longitude', place.longitude.toString());
        
        // 自定义提示词（优先级最高）
        if (customPrompt) {
            formData.append('custom_prompt', customPrompt);
        }
        
        // 调用后端API
        const response = await fetch('/api/generate-attraction-photo', {
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
            showGeneratedPhoto(result.data);
            logger.success(`✅ ${place.name}合影照片生成成功！`);
        } else {
            throw new Error(result.message || '生成失败');
        }
        
    } catch (error) {
        logger.error(`❌ 生成合影照片失败: ${error.message}`);
        alert(`生成失败: ${error.message}`);
    } finally {
        // 隐藏加载状态
        generateBtn.disabled = false;
        loadingIndicator.style.display = 'none';
    }
}

function showGeneratedPhoto(data) {
    const resultSection = document.getElementById('resultSection');
    const resultImage = document.getElementById('resultImage');
    
    // 显示生成的图片
    resultImage.src = data.base64;
    resultSection.style.display = 'block';
    
    // 存储结果数据以供下载使用
    window.generatedPhotoData = data;
    
    // 滚动到结果区域
    resultSection.scrollIntoView({ behavior: 'smooth' });
}

function downloadGeneratedPhoto() {
    if (!window.generatedPhotoData) {
        alert('没有可下载的照片');
        return;
    }
    
    const data = window.generatedPhotoData;
    
    // 创建下载链接
    const link = document.createElement('a');
    link.href = data.base64;
    link.download = data.filename || `${data.attraction}_合影_${new Date().getTime()}.png`;
    
    // 触发下载
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    logger.success(`📥 合影照片已下载: ${link.download}`);
}

function regeneratePhoto() {
    const resultSection = document.getElementById('resultSection');
    resultSection.style.display = 'none';
    window.generatedPhotoData = null;
    
    logger.info('🔄 准备重新生成合影照片');
}

// 暴露新的全局函数
window.playVideo = playVideo;
window.closeVideoModal = closeVideoModal;
window.showImageModal = showImageModal;
window.closeImageModal = closeImageModal;
window.openSelfieGenerator = openSelfieGenerator;
window.closeSelfieGenerator = closeSelfieGenerator;
window.changePhoto = changePhoto;
window.generateAttractionPhoto = generateAttractionPhoto;
window.downloadGeneratedPhoto = downloadGeneratedPhoto;
window.regeneratePhoto = regeneratePhoto;