# modules/threads_client.py

import time
import logging

# 從使用者提供的情報中獲取的靜態 ID
_LIKE_DOC_ID = "25607581692163017"
_APP_ID = "238260118697367"

def like_post(driver, post_id: str) -> bool:
    """
    [核心互動功能 V4 - 終極版]
    動態提取頁面中的三個安全令牌 (fb_dtsg, lsd, jazoest) 並加入請求中，
    以模擬最真實的瀏覽器按讚行為。

    :param driver: 已通過認證的 Selenium WebDriver 實例。
    :param post_id: 要按讚的貼文 ID (在 API 中被稱為 mediaID)。
    :return: 如果請求成功發送並得到伺服器 200 OK 回應，則返回 True，否則返回 False。
    """
    if not driver or not post_id:
        logging.error("[Like Client] 缺少 driver 或 post_id。")
        return False

    # 將腳本拆分為兩部分來避免 f-string 解析錯誤
    js_script_part1 = f"""
    const callback = arguments[arguments.length - 1];
    const mediaID = '{post_id}';
    const docID = '{_LIKE_DOC_ID}';
    const appID = '{_APP_ID}';
    """

    js_script_part2 = r"""
    // 1. 從 DOM 動態提取所有必需的安全令牌
    const fbDtsgInput = document.querySelector('input[name="fb_dtsg"]');
    const lsdInput = document.querySelector('input[name="lsd"]');
    const jazoestInput = document.querySelector('input[name="jazoest"]');

    if (!fbDtsgInput || !lsdInput || !jazoestInput) {
        console.error('[Like Client V4] 無法在頁面中找到 fb_dtsg, lsd 或 jazoest 安全令牌。');
        callback(false);
        return;
    }

    const fbDtsg = fbDtsgInput.value;
    const lsd = lsdInput.value;
    const jazoest = jazoestInput.value;

    // 2. 準備請求的 Body
    const variables = JSON.stringify({mediaID: mediaID});
    const formBody = new URLSearchParams();
    formBody.append('fb_dtsg', fbDtsg);
    formBody.append('lsd', lsd);
    formBody.append('jazoest', jazoest);
    formBody.append('doc_id', docID);
    formBody.append('variables', variables);
    formBody.append('server_timestamps', 'true');

    console.log(`[Like Client V4] 準備為 Post ID: ${mediaID} 按讚 (使用終極令牌)...`);

    // 3. 發送帶有完整令牌的 Fetch 請求
    fetch('/api/graphql', {
        "method": "POST",
        "headers": {
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "X-IG-App-ID": appID,
            "X-FB-Friendly-Name": "useTHLikeMutationLikeMutation"
        },
        "body": formBody
    })
    .then(response => {
        console.log(`[Like Client V4] Post ID: ${mediaID} 的按讚請求完成，伺服器回應狀態:`, response.status);
        callback(response.status === 200);
    })
    .catch(error => {
        console.error(`[Like Client V4] 為 Post ID: ${mediaID} 按讚時發生 JavaScript 錯誤:`, error);
        callback(false);
    });
    """

    js_script = js_script_part1 + js_script_part2

    try:
        logging.info(f"正在執行按讚操作 for Post ID: {post_id} (V4 終極版)...")
        success = driver.execute_async_script(js_script)
        if success:
            logging.info(f"[Like Client V4] 成功為 Post ID: {post_id} 按讚。")
        else:
            logging.warning(f"[Like Client V4] 為 Post ID: {post_id} 按讚的請求未成功。")
        return success
    except Exception as e:
        logging.error(f"[Like Client V4] 執行按讚的 JavaScript 時發生 Selenium 錯誤: {e}")
        return False

# 可以在這裡加入 unlike_post 等未來可能擴充的功能