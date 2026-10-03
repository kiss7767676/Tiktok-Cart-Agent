"""ADB based Android app integration.

This module does not bypass platform protections. It controls a user-owned
Android phone through ADB and reads the visible UI hierarchy when available.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from pathlib import Path
from shutil import which
from urllib.parse import quote_plus
from xml.etree import ElementTree

from oss_my.domain.models import (
    EmulatorAppStatus,
    EmulatorScreenshot,
    EmulatorStatus,
    Platform,
    ProductSummary,
)

MARKETPLACE_PACKAGE_CANDIDATES = {
    "shopee": ("com.shopee.my", "com.shopee", "com.shopee.id", "com.shopee.ph"),
    "tiktok": ("com.zhiliaoapp.musically", "com.ss.android.ugc.trill", "com.tiktok.shop"),
}

def emulator_status(device_serial: str | None = None) -> EmulatorStatus:
    adb_path = _find_tool("adb.exe", "Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe") or _find_sdk_tool(
        "platform-tools/adb.exe"
    )
    scrcpy_path = _find_tool("scrcpy.exe", "Genymobile.scrcpy_Microsoft.Winget.Source_8wekyb3d8bbwe")
    devices = _adb_devices(adb_path) if adb_path else ()
    selected_device = _select_device(devices, device_serial)
    ready = bool(adb_path and selected_device)

    if not adb_path:
        message = "ADB is not installed or not found."
    elif not devices:
        message = "ADB is installed, but no Android phone is connected. Enable USB debugging and authorize this computer."
    elif device_serial and not selected_device:
        message = f"Selected phone `{device_serial}` was not found. Available phones: {', '.join(devices)}."
    elif len(devices) > 1 and not device_serial:
        message = f"Multiple Android phones connected. Select one: {', '.join(devices)}."
    else:
        message = f"Android phone `{selected_device}` is ready for inline preview."

    return EmulatorStatus(
        adb_path=adb_path,
        scrcpy_path=scrcpy_path,
        devices=devices,
        ready=ready,
        message=message,
    )


def start_sdk_emulator(avd_name: str = "oss_my_api35") -> EmulatorStatus:
    emulator_path = _find_sdk_tool("emulator/emulator.exe")
    status = emulator_status()
    if status.devices:
        return EmulatorStatus(
            adb_path=status.adb_path,
            scrcpy_path=status.scrcpy_path,
            devices=status.devices,
            ready=True,
            message=f"Android phone already connected: {', '.join(status.devices)}",
        )
    if not emulator_path:
        return EmulatorStatus(
            adb_path=status.adb_path,
            scrcpy_path=status.scrcpy_path,
            devices=status.devices,
            ready=False,
            message="Android SDK emulator.exe was not found. Install Android SDK emulator packages first.",
        )

    creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    subprocess.Popen(
        [
            emulator_path,
            "-avd",
            avd_name,
            "-no-window",
            "-no-audio",
            "-no-boot-anim",
            "-no-metrics",
            "-gpu",
            "swiftshader_indirect",
            "-memory",
            "2048",
            "-no-snapshot-load",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    return EmulatorStatus(
        adb_path=status.adb_path,
        scrcpy_path=status.scrcpy_path,
        devices=status.devices,
        ready=False,
        message=f"Started Android SDK emulator `{avd_name}`. Wait for ADB to report it as ready.",
    )


def launch_scrcpy(device_serial: str | None = None) -> EmulatorStatus:
    status = emulator_status(device_serial)
    if not status.scrcpy_path or not status.devices:
        return status

    selected_device = _select_device(status.devices, device_serial)
    if not selected_device:
        return status

    subprocess.Popen(
        [
            status.scrcpy_path,
            "--serial",
            selected_device,
            "--max-size=720",
            "--window-width=360",
            "--window-height=720",
            "--window-title=OSS MY Emulator",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return EmulatorStatus(
        adb_path=status.adb_path,
        scrcpy_path=status.scrcpy_path,
        devices=status.devices,
        ready=status.ready,
        message="Launched scrcpy phone display.",
    )


def capture_screenshot(device_serial: str | None = None) -> EmulatorScreenshot:
    status = emulator_status(device_serial)
    if not status.adb_path or not status.devices:
        return EmulatorScreenshot(path=None, ready=False, message=status.message)

    selected_device = _select_device(status.devices, device_serial)
    if not selected_device:
        return EmulatorScreenshot(path=None, ready=False, message=status.message)

    output_dir = Path.cwd() / ".cache" / "emulator"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"phone-{_safe_filename(selected_device)}.png"

    result = subprocess.run(
        _adb_command(status.adb_path, ["exec-out", "screencap", "-p"], selected_device),
        check=False,
        capture_output=True,
        timeout=20,
    )
    if result.returncode != 0 or not result.stdout:
        remote_path = f"/sdcard/oss_my_phone_{_safe_filename(selected_device)}.png"
        shell_result = _run_adb(status.adb_path, ["shell", "screencap", "-p", remote_path], selected_device)
        pull_result = _run_adb(status.adb_path, ["pull", remote_path, str(output_path)], selected_device)
        _run_adb(status.adb_path, ["shell", "rm", remote_path], selected_device)
        if shell_result.returncode == 0 and pull_result.returncode == 0 and output_path.exists():
            return EmulatorScreenshot(
                path=str(output_path),
                ready=True,
                message="Captured inline phone screenshot through adb pull fallback.",
            )
        message = result.stderr.decode(errors="replace").strip() or "ADB screenshot capture failed."
        return EmulatorScreenshot(path=None, ready=False, message=message)

    output_path.write_bytes(result.stdout)
    return EmulatorScreenshot(
        path=str(output_path),
        ready=True,
        message="Captured inline phone screenshot.",
    )


def tap_screen(x: int, y: int, device_serial: str | None = None) -> EmulatorStatus:
    status = emulator_status(device_serial)
    if not status.adb_path or not status.devices:
        return status

    selected_device = _select_device(status.devices, device_serial)
    if not selected_device:
        return status

    _run_adb(status.adb_path, ["shell", "input", "tap", str(max(0, x)), str(max(0, y))], selected_device)
    return EmulatorStatus(
        adb_path=status.adb_path,
        scrcpy_path=status.scrcpy_path,
        devices=status.devices,
        ready=status.ready,
        message=f"Tapped phone `{selected_device}` at {x}, {y}.",
    )


def swipe_screen(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    duration_ms: int = 350,
    device_serial: str | None = None,
) -> EmulatorStatus:
    status = emulator_status(device_serial)
    if not status.adb_path or not status.devices:
        return status

    selected_device = _select_device(status.devices, device_serial)
    if not selected_device:
        return status

    _run_adb(
        status.adb_path,
        [
            "shell",
            "input",
            "swipe",
            str(max(0, x1)),
            str(max(0, y1)),
            str(max(0, x2)),
            str(max(0, y2)),
            str(max(50, duration_ms)),
        ],
        selected_device,
    )
    return EmulatorStatus(
        adb_path=status.adb_path,
        scrcpy_path=status.scrcpy_path,
        devices=status.devices,
        ready=status.ready,
        message=f"Swiped phone `{selected_device}` from {x1}, {y1} to {x2}, {y2}.",
    )


def optimize_emulator(device_serial: str | None = None) -> EmulatorStatus:
    status = emulator_status(device_serial)
    if not status.adb_path or not status.devices:
        return status

    selected_device = _select_device(status.devices, device_serial)
    if not selected_device:
        return status

    commands = (
        ["shell", "settings", "put", "global", "window_animation_scale", "0"],
        ["shell", "settings", "put", "global", "transition_animation_scale", "0"],
        ["shell", "settings", "put", "global", "animator_duration_scale", "0"],
        ["shell", "settings", "put", "system", "screen_off_timeout", "1800000"],
    )
    for command in commands:
        _run_adb(status.adb_path, list(command), selected_device)

    return EmulatorStatus(
        adb_path=status.adb_path,
        scrcpy_path=status.scrcpy_path,
        devices=status.devices,
        ready=status.ready,
        message=f"Prepared phone `{selected_device}`: animations disabled and screen timeout extended.",
    )


def install_apk(apk_path: str, device_serial: str | None = None) -> EmulatorStatus:
    status = emulator_status(device_serial)
    if not status.adb_path or not status.devices:
        return status

    selected_device = _select_device(status.devices, device_serial)
    if not selected_device:
        return status

    resolved_apk = Path(apk_path).expanduser().resolve()
    if not resolved_apk.exists():
        return EmulatorStatus(
            adb_path=status.adb_path,
            scrcpy_path=status.scrcpy_path,
            devices=status.devices,
            ready=False,
            message=f"APK not found: {resolved_apk}",
        )

    result = _run_adb(status.adb_path, ["install", "-r", str(resolved_apk)], selected_device, timeout=120)
    message = result.stdout.strip() or result.stderr.strip() or "APK install finished."
    return EmulatorStatus(
        adb_path=status.adb_path,
        scrcpy_path=status.scrcpy_path,
        devices=status.devices,
        ready=result.returncode == 0,
        message=message,
    )


def open_marketplace_app(platform: str, device_serial: str | None = None) -> EmulatorStatus:
    status = emulator_status(device_serial)
    if not status.adb_path or not status.devices:
        return status

    selected_device = _select_device(status.devices, device_serial)
    if not selected_device:
        return status

    package_name = _resolve_marketplace_package(status.adb_path, platform, selected_device)
    if not package_name:
        return EmulatorStatus(
            adb_path=status.adb_path,
            scrcpy_path=status.scrcpy_path,
            devices=status.devices,
            ready=False,
            message=f"Unknown marketplace platform: {platform}",
        )

    package_status = _package_status(status.adb_path, platform, package_name, selected_device)
    if not package_status.installed:
        return EmulatorStatus(
            adb_path=status.adb_path,
            scrcpy_path=status.scrcpy_path,
            devices=status.devices,
            ready=False,
            message=f"{platform} app is not installed on phone `{selected_device}`.",
        )

    _run_adb(
        status.adb_path,
        ["shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"],
        selected_device,
    )
    return EmulatorStatus(
        adb_path=status.adb_path,
        scrcpy_path=status.scrcpy_path,
        devices=status.devices,
        ready=True,
        message=f"Opened {platform} app on phone `{selected_device}`.",
    )


def marketplace_app_statuses(device_serial: str | None = None) -> tuple[EmulatorAppStatus, ...]:
    status = emulator_status(device_serial)
    if not status.adb_path or not status.devices:
        return tuple(
            EmulatorAppStatus(
                platform=platform,
                package_name=candidates[0],
                installed=False,
                message=status.message,
            )
            for platform, candidates in MARKETPLACE_PACKAGE_CANDIDATES.items()
        )

    selected_device = _select_device(status.devices, device_serial)
    if not selected_device:
        return tuple(
            EmulatorAppStatus(
                platform=platform,
                package_name=candidates[0],
                installed=False,
                message=status.message,
            )
            for platform, candidates in MARKETPLACE_PACKAGE_CANDIDATES.items()
        )

    return tuple(
        _package_status(
            status.adb_path,
            platform,
            _resolve_marketplace_package(status.adb_path, platform, selected_device),
            selected_device,
        )
        for platform in MARKETPLACE_PACKAGE_CANDIDATES
    )


def search_products_in_emulator(query: str, group: str, device_serial: str | None = None) -> list[ProductSummary]:
    status = emulator_status(device_serial)
    if not status.adb_path or not status.devices:
        return [_status_card(query, group, status.message)]

    selected_device = _select_device(status.devices, device_serial)
    if not selected_device:
        return [_status_card(query, group, status.message)]

    _open_shopee_search(status.adb_path, query, group, selected_device)
    time.sleep(4)

    # Sort toggling inside Shopee app is UI/version dependent. For now, the app
    # launches the query and extracts visible rows; group is tracked in the table.
    hierarchy = _dump_ui_hierarchy(status.adb_path, selected_device)
    products = _parse_products_from_hierarchy(query, group, hierarchy)
    if products:
        return products
    return [
        _status_card(
            query,
            group,
            "Search opened in emulator, but no product-like rows were extracted from the visible UI.",
        )
    ]


def _find_tool(executable: str, package_dir_name: str) -> str | None:
    found = which(executable)
    if found:
        return found

    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return None

    package_root = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages" / package_dir_name
    if not package_root.exists():
        return None

    matches = list(package_root.rglob(executable))
    return str(matches[0]) if matches else None


def _find_sdk_tool(relative_path: str) -> str | None:
    candidates = [
        os.environ.get("ANDROID_SDK_ROOT"),
        os.environ.get("ANDROID_HOME"),
        str(Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk"),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        tool = Path(candidate) / Path(relative_path)
        if tool.exists():
            return str(tool)
    return None


def _adb_devices(adb_path: str) -> tuple[str, ...]:
    result = _run_adb(adb_path, ["devices"])
    devices = []
    for line in result.stdout.splitlines():
        if "\tdevice" in line:
            serial = line.split("\t", maxsplit=1)[0]
            if _is_physical_phone_serial(serial):
                devices.append(serial)
    return tuple(devices)


def _select_device(devices: tuple[str, ...], device_serial: str | None) -> str | None:
    if device_serial:
        return device_serial if device_serial in devices else None
    if len(devices) == 1:
        return devices[0]
    return None


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value)


def _is_physical_phone_serial(serial: str) -> bool:
    """Return True for ADB serials that look like a physical phone.

    Android emulators normally appear as `emulator-5554` or localhost TCP
    endpoints such as `127.0.0.1:5555`. The current MVP is physical-phone
    first, so phone commands intentionally ignore those emulator serials.
    """

    lowered = serial.lower()
    return not lowered.startswith(("emulator-", "127.", "localhost:", "[::1]:"))


def _installed_packages(adb_path: str, device_serial: str) -> tuple[str, ...]:
    result = _run_adb(adb_path, ["shell", "pm", "list", "packages"], device_serial)
    packages = []
    for line in result.stdout.splitlines():
        if line.startswith("package:"):
            packages.append(line.removeprefix("package:").strip())
    return tuple(packages)


def _resolve_marketplace_package(adb_path: str, platform: str, device_serial: str) -> str:
    candidates = MARKETPLACE_PACKAGE_CANDIDATES.get(platform.lower(), ())
    installed = set(_installed_packages(adb_path, device_serial))
    for candidate in candidates:
        if candidate in installed:
            return candidate

    platform_token = platform.lower()
    for package_name in installed:
        if platform_token in package_name.lower():
            return package_name

    return candidates[0] if candidates else platform


def _package_status(adb_path: str, platform: str, package_name: str, device_serial: str) -> EmulatorAppStatus:
    result = _run_adb(adb_path, ["shell", "pm", "path", package_name], device_serial)
    installed = result.returncode == 0 and package_name in result.stdout
    return EmulatorAppStatus(
        platform=platform,
        package_name=package_name,
        installed=installed,
        message="Installed" if installed else f"Not installed on phone `{device_serial}`.",
    )


def _open_shopee_search(adb_path: str, query: str, group: str, device_serial: str) -> None:
    package_name = _resolve_marketplace_package(adb_path, "shopee", device_serial)
    if _package_status(adb_path, "shopee", package_name, device_serial).installed:
        _run_adb(
            adb_path,
            ["shell", "monkey", "-p", package_name, "-c", "android.intent.category.LAUNCHER", "1"],
            device_serial,
        )
        time.sleep(3)
        if _tap_shopee_search_box(adb_path, device_serial):
            time.sleep(1)
            _clear_focused_text(adb_path, device_serial)
            _run_adb(adb_path, ["shell", "input", "text", _adb_input_text(query)], device_serial)
            time.sleep(0.5)
            _run_adb(adb_path, ["shell", "input", "keyevent", "ENTER"], device_serial)
            time.sleep(5)
            if group == "top_sales":
                _tap_text(adb_path, device_serial, "Top Sales")
                time.sleep(3)
        return

    search_url = f"https://shopee.com.my/search?keyword={quote_plus(query)}"
    _run_adb(
        adb_path,
        [
            "shell",
            "am",
            "start",
            "-a",
            "android.intent.action.VIEW",
            "-d",
            search_url,
        ],
        device_serial,
    )


def _tap_text(adb_path: str, device_serial: str, text: str) -> bool:
    hierarchy = _dump_ui_hierarchy(adb_path, device_serial)
    target = _first_node_center(hierarchy, text_fragments=(text,))
    if not target:
        return False
    x, y = target
    result = _run_adb(adb_path, ["shell", "input", "tap", str(x), str(y)], device_serial)
    return result.returncode == 0


def _dump_ui_hierarchy(adb_path: str, device_serial: str) -> str:
    _run_adb(adb_path, ["shell", "uiautomator", "dump", "/sdcard/window.xml"], device_serial)
    result = _run_adb(adb_path, ["exec-out", "cat", "/sdcard/window.xml"], device_serial)
    return result.stdout


def _tap_shopee_search_box(adb_path: str, device_serial: str) -> bool:
    hierarchy = _dump_ui_hierarchy(adb_path, device_serial)
    target = _first_node_center(
        hierarchy,
        content_descriptions=("pre_search_label", "search_bar_view"),
        text_fragments=("search",),
    )
    if not target:
        return False

    x, y = target
    result = _run_adb(adb_path, ["shell", "input", "tap", str(x), str(y)], device_serial)
    return result.returncode == 0


def _first_node_center(
    hierarchy: str,
    content_descriptions: tuple[str, ...] = (),
    text_fragments: tuple[str, ...] = (),
) -> tuple[int, int] | None:
    try:
        root = ElementTree.fromstring(hierarchy)
    except ElementTree.ParseError:
        return None

    text_needles = tuple(fragment.lower() for fragment in text_fragments)
    for node in root.iter("node"):
        description = node.attrib.get("content-desc", "")
        text = node.attrib.get("text", "")
        if description in content_descriptions or any(fragment in text.lower() for fragment in text_needles):
            center = _bounds_center(node.attrib.get("bounds", ""))
            if center:
                return center
    return None


def _bounds_center(bounds: str) -> tuple[int, int] | None:
    match = re.fullmatch(r"\[(\d+),(\d+)]\[(\d+),(\d+)]", bounds)
    if not match:
        return None
    left, top, right, bottom = (int(value) for value in match.groups())
    return ((left + right) // 2, (top + bottom) // 2)


def _clear_focused_text(adb_path: str, device_serial: str, max_chars: int = 80) -> None:
    for _ in range(max_chars):
        _run_adb(adb_path, ["shell", "input", "keyevent", "DEL"], device_serial)


def _adb_input_text(value: str) -> str:
    escaped = []
    for character in value:
        if character.isspace():
            escaped.append("%s")
        elif character in {'"', "'", "\\", "&", "|", ";", "<", ">", "(", ")", "$", "`"}:
            escaped.append("")
        else:
            escaped.append(character)
    return "".join(escaped)


def _run_adb(
    adb_path: str,
    args: list[str],
    device_serial: str | None = None,
    timeout: float = 20,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        _adb_command(adb_path, args, device_serial),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _adb_command(adb_path: str, args: list[str], device_serial: str | None = None) -> list[str]:
    command = [adb_path]
    if device_serial:
        command.extend(["-s", device_serial])
    command.extend(args)
    return command


def _parse_products_from_hierarchy(query: str, group: str, hierarchy: str) -> list[ProductSummary]:
    try:
        root = ElementTree.fromstring(hierarchy)
    except ElementTree.ParseError:
        return []

    texts = [
        value.strip()
        for node in root.iter("node")
        for value in [node.attrib.get("text", "")]
        if value and value.strip()
    ]
    return _parse_products_from_texts(query, group, texts)


def _parse_products_from_texts(query: str, group: str, texts: list[str]) -> list[ProductSummary]:
    products = []
    current_title: str | None = None
    current_price: str | None = None
    current_meta: list[str] = []
    filter_labels = {"filter", "relevance", "latest", "top sales", "price"}
    has_filter_bar = any(text.strip().lower() in filter_labels for text in texts)
    passed_filter_bar = not has_filter_bar

    for text in texts:
        if text.strip().lower() in filter_labels:
            passed_filter_bar = True
            continue
        if not passed_filter_bar:
            continue

        if _looks_like_price(text):
            if current_title and not current_price:
                current_price = text
            continue

        if _looks_like_meta(text):
            current_meta.append(text)
            continue

        if _looks_like_product_title(text, query):
            if current_title:
                products.append(_summary_from_visible_text(query, group, current_title, current_price, current_meta))
                current_meta = []
                current_price = None
            current_title = text

    if current_title:
        products.append(_summary_from_visible_text(query, group, current_title, current_price, current_meta))

    return products[:12]


def _summary_from_visible_text(
    query: str,
    group: str,
    title: str,
    price: str | None,
    meta: list[str],
) -> ProductSummary:
    return ProductSummary(
        id=f"emulator-shopee-{group}-{abs(hash((title, price))) % 1_000_000}",
        platform=Platform.SHOPEE,
        title=title,
        product_url=f"https://shopee.com.my/search?keyword={quote_plus(query)}",
        price_label=price or "Price not visible",
        shipping_label=_first_matching(
            meta,
            ("ships from", "selangor", "kuala lumpur", "mainland china", "thailand", "taiwan"),
        )
        or "Shipping not visible",
        rating_label=_first_matching(meta, ("★", "rating", "/5")) or "Rating not visible",
        stock_label=_first_matching(meta, ("sold", "left", "available")) or "Stock/sales not visible",
        seller_label="Seller not visible",
        data_status="emulator_visible_text",
        result_group=_group_label(group),
        risk_notes=("Extracted from visible emulator UI; verify details in the app before checkout.",),
        research_queries=(title, f"{title} review", f"{query} Malaysia"),
    )


def _status_card(query: str, group: str, message: str) -> ProductSummary:
    return ProductSummary(
        id=f"emulator-shopee-{group}-status",
        platform=Platform.SHOPEE,
        title=f"Emulator search status: {_group_label(group)}",
        product_url=f"https://shopee.com.my/search?keyword={quote_plus(query)}",
        price_label="No extracted price",
        shipping_label=message,
        rating_label="No extracted rating",
        stock_label="No extracted sales/stock",
        seller_label="No extracted seller",
        data_status="emulator_status",
        result_group=_group_label(group),
        risk_notes=(message,),
        research_queries=(query, f"{query} review", f"{query} Malaysia"),
    )


def _looks_like_price(text: str) -> bool:
    lowered = text.lower().strip()
    if "rm" in lowered:
        return bool(re.search(r"rm\s*\d+(\.\d{1,2})?", lowered, flags=re.IGNORECASE))
    return False


def _looks_like_meta(text: str) -> bool:
    lowered = text.lower()
    if re.fullmatch(r"[0-5](\.\d)?", lowered):
        return True
    if any(token in lowered for token in ("thailand", "taiwan")):
        return True
    return any(token in lowered for token in ("sold", "left", "ships", "rating", "selangor", "kuala lumpur", "china", "★", "/5"))


def _looks_like_product_title(text: str, query: str) -> bool:
    if len(text) < 8:
        return False
    lowered = text.lower()
    query_tokens = [token for token in query.lower().split() if len(token) >= 3]
    return any(token in lowered for token in query_tokens)


def _first_matching(values: list[str], needles: tuple[str, ...]) -> str | None:
    for value in values:
        lowered = value.lower()
        if "/5" in needles and re.fullmatch(r"[0-5](\.\d)?", lowered):
            return value
        if any(needle in lowered for needle in needles):
            return value
    return None


def _group_label(group: str) -> str:
    return "Top sales" if group == "top_sales" else "Most relevant"
