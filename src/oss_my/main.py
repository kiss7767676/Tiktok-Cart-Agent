"""Command-line entry point for the teachable backend.

The final product should have a fast native desktop UI. This CLI exists so we
can build and test the system logic in small, understandable pieces first.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from oss_my import __version__
from oss_my.platforms import detect_link
from oss_my.services import (
    account_setup_statuses,
    best_buy_search,
    build_checkout_plan,
    build_research_brief,
    emulator_app_statuses,
    emulator_best_buy_search,
    get_emulator_screenshot,
    get_emulator_status,
    get_product_details,
    install_emulator_apk,
    open_account_login,
    open_emulator_display,
    optimize_emulator_runtime,
    parse_platforms,
    start_emulator,
    store_account_credentials,
    swipe_emulator,
    tap_emulator,
)

app = typer.Typer(help="Online Shopping System Malaysia backend tools.")
console = Console()


@app.command()
def version() -> None:
    """Print the backend version."""

    console.print(__version__)


@app.command()
def detect(
    urls: Annotated[
        list[str],
        typer.Argument(help="One or more Shopee/TikTok/Lazada product links."),
    ],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for future UI integration."),
    ] = False,
) -> None:
    """Detect marketplace links and parse product identity where possible."""

    results = [detect_link(url) for url in urls]

    if json_output:
        console.print_json(data=[_to_jsonable(result) for result in results])
        return

    table = Table(title="Detected Shopping Links")
    table.add_column("Platform")
    table.add_column("MVP")
    table.add_column("Shop ID")
    table.add_column("Item ID")
    table.add_column("Notes")

    for result in results:
        identity = result.product_identity
        table.add_row(
            result.platform.value,
            "yes" if result.is_supported_for_mvp else "no",
            identity.shop_id if identity else "-",
            identity.item_id if identity else "-",
            "\n".join(result.notes) if result.notes else "-",
        )

    console.print(table)


@app.command("best-buy")
def best_buy(
    query: Annotated[str, typer.Argument(help="Product keyword or purchase intent.")],
    platform: Annotated[
        list[str] | None,
        typer.Option(
            "--platform",
            "-p",
            help="Platform to include. Repeat for multiple. Defaults to Shopee and TikTok.",
        ),
    ] = None,
    budget_min: Annotated[
        float | None,
        typer.Option("--budget-min", help="Minimum budget in RM."),
    ] = None,
    budget_max: Annotated[
        float | None,
        typer.Option("--budget-max", help="Maximum budget in RM."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Find Best Buy candidates or platform handoff cards."""

    results = best_buy_search(query, parse_platforms(platform or []), budget_min, budget_max)
    if json_output:
        console.print_json(data=[_to_jsonable(result) for result in results])
        return

    table = Table(title="Best Buy")
    table.add_column("Platform")
    table.add_column("Title")
    table.add_column("Price")
    table.add_column("Status")
    table.add_column("URL")

    for result in results:
        table.add_row(
            result.platform.value,
            result.title,
            result.price_label,
            result.data_status,
            result.product_url,
        )

    console.print(table)


@app.command("emulator-status")
def emulator_status_command(
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Show Android emulator/device status."""

    status = get_emulator_status(device)
    if json_output:
        console.print_json(data=_to_jsonable(status))
        return
    console.print(f"ADB: {status.adb_path or '-'}")
    console.print(f"scrcpy: {status.scrcpy_path or '-'}")
    console.print(f"Devices: {', '.join(status.devices) or '-'}")
    console.print(f"Ready: {status.ready}")
    console.print(status.message)


@app.command("phone-status")
def phone_status_command(
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Show connected Android phone status."""

    emulator_status_command(device=device, json_output=json_output)


@app.command("emulator-display")
def emulator_display(
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Launch a small scrcpy phone display for the connected emulator/device."""

    status = open_emulator_display(device)
    if json_output:
        console.print_json(data=_to_jsonable(status))
        return
    console.print(status.message)


@app.command("emulator-screenshot")
def emulator_screenshot(
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Capture a phone screenshot for the inline desktop emulator panel."""

    screenshot = get_emulator_screenshot(device)
    if json_output:
        console.print_json(data=_to_jsonable(screenshot))
        return
    console.print(screenshot.message)
    if screenshot.path:
        console.print(screenshot.path)


@app.command("phone-screenshot")
def phone_screenshot(
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Capture a connected phone screenshot for the desktop preview."""

    emulator_screenshot(device=device, json_output=json_output)


@app.command("emulator-start")
def emulator_start(
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Start the standalone Android SDK emulator headlessly."""

    status = start_emulator()
    if json_output:
        console.print_json(data=_to_jsonable(status))
        return
    console.print(status.message)


@app.command("emulator-tap")
def emulator_tap(
    x: Annotated[int, typer.Argument(help="Device X coordinate.")],
    y: Annotated[int, typer.Argument(help="Device Y coordinate.")],
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Tap the emulator screen through ADB."""

    status = tap_emulator(x, y, device)
    if json_output:
        console.print_json(data=_to_jsonable(status))
        return
    console.print(status.message)


@app.command("phone-tap")
def phone_tap(
    x: Annotated[int, typer.Argument(help="Device X coordinate.")],
    y: Annotated[int, typer.Argument(help="Device Y coordinate.")],
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Tap the connected phone screen through ADB."""

    emulator_tap(x=x, y=y, device=device, json_output=json_output)


@app.command("emulator-swipe")
def emulator_swipe(
    x1: Annotated[int, typer.Argument(help="Start X coordinate.")],
    y1: Annotated[int, typer.Argument(help="Start Y coordinate.")],
    x2: Annotated[int, typer.Argument(help="End X coordinate.")],
    y2: Annotated[int, typer.Argument(help="End Y coordinate.")],
    duration_ms: Annotated[int, typer.Option("--duration-ms", help="Swipe duration.")] = 350,
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Swipe the emulator screen through ADB."""

    status = swipe_emulator(x1, y1, x2, y2, duration_ms, device)
    if json_output:
        console.print_json(data=_to_jsonable(status))
        return
    console.print(status.message)


@app.command("phone-swipe")
def phone_swipe(
    x1: Annotated[int, typer.Argument(help="Start X coordinate.")],
    y1: Annotated[int, typer.Argument(help="Start Y coordinate.")],
    x2: Annotated[int, typer.Argument(help="End X coordinate.")],
    y2: Annotated[int, typer.Argument(help="End Y coordinate.")],
    duration_ms: Annotated[int, typer.Option("--duration-ms", help="Swipe duration.")] = 350,
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Swipe the connected phone screen through ADB."""

    emulator_swipe(
        x1=x1,
        y1=y1,
        x2=x2,
        y2=y2,
        duration_ms=duration_ms,
        device=device,
        json_output=json_output,
    )


@app.command("emulator-optimize")
def emulator_optimize(
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Apply runtime emulator speed settings."""

    status = optimize_emulator_runtime(device)
    if json_output:
        console.print_json(data=_to_jsonable(status))
        return
    console.print(status.message)


@app.command("phone-optimize")
def phone_optimize(
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Apply connected phone runtime settings useful for automation."""

    emulator_optimize(device=device, json_output=json_output)


@app.command("emulator-apps")
def emulator_apps(
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Show whether required marketplace apps are installed in the emulator."""

    statuses = emulator_app_statuses(device)
    if json_output:
        console.print_json(data=[_to_jsonable(status) for status in statuses])
        return

    table = Table(title="Emulator Apps")
    table.add_column("Platform")
    table.add_column("Package")
    table.add_column("Installed")
    table.add_column("Message")
    for status in statuses:
        table.add_row(
            status.platform,
            status.package_name,
            "yes" if status.installed else "no",
            status.message,
        )
    console.print(table)


@app.command("phone-apps")
def phone_apps(
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Show whether required marketplace apps are installed on the connected phone."""

    emulator_apps(device=device, json_output=json_output)


@app.command("emulator-install-apk")
def emulator_install_apk(
    apk_path: Annotated[str, typer.Argument(help="Path to an APK file to install.")],
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Install a local APK into the emulator through ADB."""

    status = install_emulator_apk(apk_path, device)
    if json_output:
        console.print_json(data=_to_jsonable(status))
        return
    console.print(status.message)


@app.command("phone-install-apk")
def phone_install_apk(
    apk_path: Annotated[str, typer.Argument(help="Path to an APK file to install.")],
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Install a local APK into the connected phone through ADB."""

    emulator_install_apk(apk_path=apk_path, device=device, json_output=json_output)


@app.command("emulator-open-app")
def emulator_open_app(
    platform: Annotated[str, typer.Argument(help="Platform to open: shopee or tiktok.")],
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Open a marketplace app in the emulator if installed."""

    parsed = parse_platforms([platform])[0]
    status = open_account_login(parsed, device)
    if json_output:
        console.print_json(data=_to_jsonable(status))
        return
    console.print(status.message)


@app.command("phone-open-app")
def phone_open_app(
    platform: Annotated[str, typer.Argument(help="Platform to open: shopee or tiktok.")],
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Open a marketplace app on the connected phone if installed."""

    emulator_open_app(platform=platform, device=device, json_output=json_output)


@app.command("emulator-best-buy")
def emulator_best_buy(
    query: Annotated[str, typer.Argument(help="Product keyword or purchase intent.")],
    group: Annotated[
        str,
        typer.Option("--group", help="Result group: relevancy or top_sales."),
    ] = "relevancy",
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Search using the connected Android emulator/device and extract visible products."""

    results = emulator_best_buy_search(query, group, device)
    if json_output:
        console.print_json(data=[_to_jsonable(result) for result in results])
        return

    table = Table(title=f"Emulator Best Buy: {query}")
    table.add_column("Group")
    table.add_column("Title")
    table.add_column("Price")
    table.add_column("Shipping")
    table.add_column("Status")
    for result in results:
        table.add_row(
            result.result_group,
            result.title,
            result.price_label,
            result.shipping_label,
            result.data_status,
        )
    console.print(table)


@app.command("phone-best-buy")
def phone_best_buy(
    query: Annotated[str, typer.Argument(help="Product keyword or purchase intent.")],
    group: Annotated[
        str,
        typer.Option("--group", help="Result group: relevancy or top_sales."),
    ] = "relevancy",
    device: Annotated[
        str | None,
        typer.Option("--device", help="ADB device serial to target."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Search using the connected Android phone and extract visible products."""

    emulator_best_buy(query=query, group=group, device=device, json_output=json_output)


@app.command()
def research(
    query: Annotated[str, typer.Argument(help="Product or purchase topic to research.")],
    scrape_google: Annotated[
        bool,
        typer.Option("--scrape-google/--no-scrape-google", help="Use own Google scraper."),
    ] = True,
    use_ollama: Annotated[
        bool,
        typer.Option("--ollama/--no-ollama", help="Ask a local Ollama model for a research response."),
    ] = True,
    ollama_model: Annotated[
        str | None,
        typer.Option("--ollama-model", help="Ollama model name. Defaults to OSS_MY_OLLAMA_MODEL or llama3.2."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Build a research helper for conscious purchase decisions."""

    brief = build_research_brief(
        query,
        scrape_google=scrape_google,
        use_ollama=use_ollama,
        ollama_model=ollama_model,
    )
    if json_output:
        console.print_json(data=_to_jsonable(brief))
        return

    console.print(f"[bold]Research:[/bold] {brief.query}")
    console.print(brief.overview)
    console.print("\n[bold]Key questions[/bold]")
    for question in brief.key_questions:
        console.print(f"- {question}")
    console.print("\n[bold]Sources[/bold]")
    for link in brief.source_links:
        console.print(f"- {link}")
    console.print(f"\n[bold]Ollama status:[/bold] {brief.ollama_status}")
    if brief.ollama_response:
        console.print(f"\n[bold]Ollama response ({brief.ollama_model})[/bold]\n{brief.ollama_response}")
    console.print(f"\n[bold]Google scrape status:[/bold] {brief.scrape_status}")
    if brief.google_ai_overview:
        console.print(f"\n[bold]Google AI Overview[/bold]\n{brief.google_ai_overview}")
    if brief.scraped_sources:
        console.print("\n[bold]Scraped sources[/bold]")
        for source in brief.scraped_sources:
            console.print(f"- {source.title}: {source.url}")


@app.command("checkout-plan")
def checkout_plan(
    urls: Annotated[list[str], typer.Argument(help="Selected product/search links.")],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Build a user-supervised checkout handoff plan."""

    plan = build_checkout_plan(urls)
    if json_output:
        console.print_json(data=_to_jsonable(plan))
        return

    console.print(f"[bold]Platform:[/bold] {plan.platform.value}")
    console.print(f"[bold]Items:[/bold] {plan.item_count}")
    console.print(f"[bold]Checkout URL:[/bold] {plan.checkout_url or '-'}")
    for warning in plan.warnings:
        console.print(f"- {warning}")


@app.command("product-details")
def product_details(
    urls: Annotated[list[str], typer.Argument(help="Product links to inspect.")],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Fetch product details for supported platforms."""

    details = get_product_details(urls)
    if json_output:
        console.print_json(data=[_to_jsonable(detail) for detail in details])
        return

    for detail in details:
        console.print(f"[bold]{detail.title}[/bold]")
        console.print(f"Platform: {detail.platform.value}")
        console.print(f"Price: {detail.price_label}")
        console.print(f"Rating: {detail.rating_label}")
        console.print(f"Sold: {detail.sold_label}")
        console.print(f"Stock: {detail.stock_label}")
        console.print(f"Seller: {detail.shop_label}")
        console.print(f"Location: {detail.location_label}")
        for group in detail.option_groups:
            console.print(f"{group.name}: {', '.join(group.options) or '-'}")
        for warning in detail.warnings:
            console.print(f"- {warning}")
        console.print("")


@app.command("account-status")
def account_status(
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Show account setup status for MVP platforms."""

    statuses = account_setup_statuses()
    if json_output:
        console.print_json(data=[_to_jsonable(status) for status in statuses])
        return

    table = Table(title="Account Setup")
    table.add_column("Platform")
    table.add_column("Configured")
    table.add_column("Storage")
    table.add_column("Next action")
    for status in statuses:
        table.add_row(
            status.platform.value,
            "yes" if status.configured else "no",
            status.credential_storage,
            status.next_action,
        )
    console.print(table)


@app.command("account-set")
def account_set(
    platform: Annotated[str, typer.Argument(help="Platform: shopee or tiktok.")],
    username: Annotated[str, typer.Option("--username", prompt=True, help="Login username/email/phone.")],
    password: Annotated[
        str,
        typer.Option("--password", prompt=True, hide_input=True, help="Login password."),
    ],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Print machine-readable JSON for desktop UI integration."),
    ] = False,
) -> None:
    """Store marketplace credentials in the OS keyring."""

    parsed = parse_platforms([platform])[0]
    status = store_account_credentials(parsed, username, password)
    if json_output:
        console.print_json(data=_to_jsonable(status))
        return
    console.print(f"{parsed.value} credentials stored in OS keyring.")


def _to_jsonable(value: object) -> object:
    """Convert dataclass/enum values into JSON-friendly values."""

    if is_dataclass(value):
        return {key: _to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, tuple):
        return [_to_jsonable(item) for item in value]
    return value


def main() -> None:
    app()


if __name__ == "__main__":
    main()
