# modules/threads_client.py

import logging
import re
import json
from urllib.parse import quote

def get_like_tokens(page_source: str) -> tuple[str | None, str | None]:
    """
    [V2 新增] 從頁面原始碼中提取按讚 API 所需的 CSRF 和 LSD 權杖。
    """
    logging.info("[Auth] 正在嘗試從頁面中提取 API 權杖...")
    try:
        csrf_token_match = re.search(r'"csrf_token":"(.*?)"', page_source)
        lsd_token_match = re.search(r'"LSD",\[\],{"token":"(.*?)"}', page_source)
        
        csrf_token = csrf_token_match.group(1) if csrf_token_match else None
        lsd_token = lsd_token_match.group(1) if lsd_token_match else None

        if csrf_token and lsd_token:
            logging.info(f"[Auth] 成功提取權杖！CSRF: {csrf_token[:5]}..., LSD: {lsd_token[:5]}...")
            return csrf_token, lsd_token
        else:
            logging.error("[Auth] 提取權杖失敗，無法執行按讚操作。")
            return None, None
    except Exception as e:
        logging.error(f"[Auth] 提取權杖時發生未知錯誤: {e}")
        return None, None

def like_post(driver, post_id: str, csrf_token: str, lsd_token: str) -> bool:
    """
    [V2 重構] 使用從瀏覽器捕獲的真實 fetch 請求來模擬按讚操作。
    直接在瀏覽器上下文中執行 JavaScript fetch，這是最可靠的方法。
    """
    if not all([post_id, csrf_token, lsd_token]):
        logging.error("[API] 按讚失敗：缺少 post_id 或必要權杖。")
        return False

    js_script = f"""
    const post_id = "{post_id}";
    const csrf_token = "{csrf_token}";
    const lsd_token = "{lsd_token}";

    const variables = {{
        "mediaID": post_id
    }};

    const body_payload = new URLSearchParams({{
        "av": "17841476390550493",
        "__user": "0",
        "__a": "1",
        "__req": "hh",
        "__hs": "20382.HYP:barcelona_web_pkg.2.1...0",
        "dpr": "1",
        "__ccg": "UNKNOWN",
        "__rev": "1028695034",
        "__s": "394t2u:udrm5q:a8voxm",
        "__hsi": "7563565871771780035",
        "__dyn": "7xeUmwlEnwn8K2Wmh0no6u5U4e0yoW3q32360CEbo1nEhw2nVE4W0qa0FE2awgo9oO0n24oaEd82lwv89k2C1Fwc60D85m1mzXwae4UaEW0Loco5G0zK5o4q0HU1IEGdwtU2ewbS1LwTwKG0hq1Iwqo9Epxq261bg5q2-2K7E4u8Dxd0LCzU4C7E7C1swnrwu813o",
        "__csr": "gjN-DtPOFn5lNDT7OlleDQGOqV5mAQhaHyQjRJbEyKAmmiRy9p_mXGVXhpAZp4UzzA481aob8qU7K1jU2Szo01u10Icwq81s40ne1Rc1mDlwcdrUvguz82h4UB2VC589o198Wm0dQDAjxC04cEgxa0rG3XwaW0azHg1_im0KU3kaHAGcC86UN03TUOPPa1TIQMaO0UwiHwqU466o-cwvU2nU4S27wvAPha6ja1xhSt2U960y84e1_gdA0KEd5N8O0UEdEbU1v8zw0v9J5wfJ5g0TG0N8uwcaXK0jt7K8DQl0",
        "__hsdp": "gdGj29gSwfYwlINNh2MOmPNA50FcZinelggjha89ybN32c4V53r6n1z358miJ3FQe1B7mR1akrQtEF4gEqGRh2B8cf4ygkLehy1Ig2ykMA82arxcM511cgQ2d10q14g3zg2hyE8vwSJ5AwBw61zo2JwgK8wbi582cwRwUwiU",
        "__hblp": "4g1j42F4wPzox5y68gS3u531y2CdxacwpA5E4V0Kxjxqu7oCUnU-1dxm22dzKchEkDLwjUkyUy6EgDG7VqxGUK2_VAu0z9FopwwDx-byEgUG4ouzUpUdo887-0U8S7U5i3yfwHVbAU-2aUc84O8yU72dV9EdotxG58dElw",
        "__sjsp": "gc5N2j29gSwfYwlINNh2x-POy0k2A8linelpgRd98S4HN32ea3xsdIodg8HUoi4CAgW5Q3XrA164U-2SpkewkrPAowr401wC",
        "__comet_req": "29",
        "fb_dtsg": "NAfuzmM0EaLTJF3BeGlX9I0Qf6KRFJNvz9mPC3ax4_QLBffhWNAsjxg:17843671327157124:1760852161",
        "jazoest": "26158",
        "lsd": lsd_token,
        "__spin_r": "1028695034",
        "__spin_b": "trunk",
        "__spin_t": "1761029910",
        "__jssesw": "2",
        "__crn": "comet.threads.BarcelonaPostColumnRoute",
        "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "useTHLikeMutationLikeMutation",
        "server_timestamps": "true",
        "variables": JSON.stringify(variables),
        "doc_id": "25607581692163017"
    }});

    const headers = {{
        "accept": "*/*",
        "content-type": "application/x-www-form-urlencoded",
        "x-asbd-id": "359341",
        "x-csrftoken": csrf_token,
        "x-fb-friendly-name": "useTHLikeMutationLikeMutation",
        "x-fb-lsd": lsd_token,
        "x-ig-app-id": "238260118697367"
    }};

    try {{
        const response = await fetch("https://www.threads.net/api/graphql", {{
            "headers": headers,
            "body": body_payload,
            "method": "POST"
        }});
        const responseData = await response.json();
        return {{ success: response.ok, status: response.status, data: responseData }};
    }} catch (error) {{
        return {{ success: false, error: error.toString() }};
    }}
    """

    try:
        logging.info(f"[API] 正在執行按讚操作，目標 Post ID: {post_id}")
        result = driver.execute_script(js_script)
        
        # 獲取瀏覽器控制台日誌
        for entry in driver.get_log('browser'):
            logging.info(f"[Browser Console] {entry['level']}: {entry['message']}")

        if result and result.get('success'):
            logging.info(f"[API] Post ID: {post_id} 按讚成功！")
            return True
        else:
            error_message = result.get('error', result.get('data', '未知錯誤'))
            logging.error(f"[API] Post ID: {post_id} 按讚失敗。伺服器回應: {error_message}")
            return False
    except Exception as e:
        logging.error(f"[API] 執行按讚的 JavaScript 時發生嚴重錯誤: {e}")
        return False