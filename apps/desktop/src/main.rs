use std::path::Path;
use std::process::{Command, Output};

use dioxus::prelude::*;
use serde::Deserialize;
use serde::de::DeserializeOwned;

fn main() {
    dioxus::launch(App);
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
enum View {
    #[default]
    BestBuy,
    BuyWithLinks,
    Research,
    AccountSetup,
}

#[derive(Clone, Copy, Debug, Default, PartialEq, Eq)]
enum ResultGroup {
    #[default]
    MostRelevant,
    TopSales,
}

impl ResultGroup {
    fn backend_value(self) -> &'static str {
        match self {
            ResultGroup::MostRelevant => "relevancy",
            ResultGroup::TopSales => "top_sales",
        }
    }

    fn label(self) -> &'static str {
        match self {
            ResultGroup::MostRelevant => "Most relevant",
            ResultGroup::TopSales => "Top sales",
        }
    }
}

#[derive(Clone, Debug, Default, Deserialize, PartialEq)]
struct DeviceStatus {
    adb_path: Option<String>,
    scrcpy_path: Option<String>,
    devices: Vec<String>,
    ready: bool,
    message: String,
}

#[derive(Clone, Debug, Default, Deserialize, PartialEq)]
struct DeviceScreenshot {
    path: Option<String>,
    ready: bool,
    message: String,
}

#[derive(Clone, Debug, Default, Deserialize, PartialEq)]
struct DeviceAppStatus {
    platform: String,
    package_name: String,
    installed: bool,
    message: String,
}

#[derive(Clone, Debug, Default, Deserialize, PartialEq)]
struct ProductSummary {
    id: String,
    platform: String,
    title: String,
    product_url: String,
    price_label: String,
    shipping_label: String,
    rating_label: String,
    stock_label: String,
    seller_label: String,
    data_status: String,
    result_group: String,
    risk_notes: Vec<String>,
    research_queries: Vec<String>,
}

#[derive(Clone, Debug, Default, Deserialize, PartialEq)]
struct ResearchSource {
    title: String,
    url: String,
    snippet: String,
    source_type: String,
}

#[derive(Clone, Debug, Default, Deserialize, PartialEq)]
struct ResearchBrief {
    query: String,
    overview: String,
    key_questions: Vec<String>,
    source_links: Vec<String>,
    cautions: Vec<String>,
    ollama_response: Option<String>,
    ollama_status: String,
    ollama_model: Option<String>,
    google_ai_overview: Option<String>,
    scraped_sources: Vec<ResearchSource>,
    scrape_status: String,
}

#[derive(Clone, Debug, PartialEq)]
struct YoutubeVideo {
    id: String,
    title: String,
    source_url: String,
}

#[derive(Clone, Debug, Default, Deserialize, PartialEq)]
struct AccountSetupStatus {
    platform: String,
    configured: bool,
    credential_storage: String,
    next_action: String,
}

#[derive(Clone, Debug, Default, Deserialize, PartialEq)]
struct ProductIdentity {
    platform: String,
    item_id: Option<String>,
    shop_id: Option<String>,
    raw_slug: Option<String>,
}

#[derive(Clone, Debug, Default, Deserialize, PartialEq)]
struct DetectedLink {
    original_url: String,
    platform: String,
    product_identity: Option<ProductIdentity>,
    is_supported_for_mvp: bool,
    notes: Vec<String>,
}

#[derive(Clone, Debug, Default, Deserialize, PartialEq)]
struct CheckoutPlan {
    platform: String,
    item_count: usize,
    checkout_url: String,
    warnings: Vec<String>,
    detected_links: Vec<DetectedLink>,
}

#[component]
fn App() -> Element {
    let mut active_view = use_signal(View::default);
    let mut status = use_signal(|| {
        "Physical phone mode. Connect your Android phone and check status.".to_owned()
    });

    let mut device_status = use_signal(DeviceStatus::default);
    let mut selected_device = use_signal(String::new);
    let mut screenshot = use_signal(Option::<DeviceScreenshot>::default);
    let mut device_apps = use_signal(Vec::<DeviceAppStatus>::new);

    let mut query = use_signal(String::new);
    let mut budget_min = use_signal(String::new);
    let mut budget_max = use_signal(String::new);
    let mut include_shopee = use_signal(|| true);
    let mut include_tiktok = use_signal(|| true);
    let mut result_group = use_signal(ResultGroup::default);
    let mut products = use_signal(Vec::<ProductSummary>::new);
    let mut selected_product = use_signal(Option::<usize>::default);

    let mut checkout_input = use_signal(String::new);
    let mut checkout_links = use_signal(Vec::<String>::new);
    let mut detected_links = use_signal(Vec::<DetectedLink>::new);
    let mut checkout_plan = use_signal(Option::<CheckoutPlan>::default);

    let mut research_query = use_signal(String::new);
    let mut research_brief = use_signal(Option::<ResearchBrief>::default);
    let mut selected_youtube_video = use_signal(Option::<YoutubeVideo>::default);

    let mut account_statuses = use_signal(Vec::<AccountSetupStatus>::new);
    let mut shopee_username = use_signal(String::new);
    let mut shopee_password = use_signal(String::new);
    let mut tiktok_username = use_signal(String::new);
    let mut tiktok_password = use_signal(String::new);
    let mut apk_path = use_signal(String::new);

    use_effect(move || {
        if let Ok(value) = run_backend_json::<DeviceStatus>(&["phone-status", "--json"]) {
            if selected_device.read().is_empty() && value.devices.len() == 1 {
                selected_device.set(value.devices[0].clone());
            }
            device_status.set(value);
        }
        if let Ok(value) = run_backend_json::<Vec<DeviceAppStatus>>(&["phone-apps", "--json"]) {
            device_apps.set(value);
        }
        if let Ok(value) =
            run_backend_json::<Vec<AccountSetupStatus>>(&["account-status", "--json"])
        {
            account_statuses.set(value);
        }
    });

    let product_rows = products.read().clone();
    let device_rows = device_status.read().devices.clone();
    let selected_device_value = selected_device();
    let checkout_count = checkout_links.read().len();
    let current_product = selected_product()
        .and_then(|index| product_rows.get(index).cloned())
        .or_else(|| product_rows.first().cloned());
    let app_rows = device_apps.read().clone();
    let account_rows = account_statuses.read().clone();
    let link_rows = detected_links.read().clone();
    let checkout_plan_value = checkout_plan.read().clone();
    let research_value = research_brief.read().clone();
    let selected_youtube_value = selected_youtube_video.read().clone();
    let phone_message = screenshot
        .read()
        .as_ref()
        .map(|shot| shot.message.clone())
        .unwrap_or_else(|| device_status.read().message.clone());
    let phone_image = screenshot
        .read()
        .as_ref()
        .and_then(|shot| shot.path.as_ref())
        .map(|path| path_to_file_url(path));

    rsx! {
        style { "{APP_CSS}" }
        div { class: "app",
            aside { class: "sidebar",
                div { class: "brand",
                    div { class: "brand_mark", "MY" }
                    div {
                        h1 { "Online Shopping" }
                        p { "Malaysia conscious-buying workspace" }
                    }
                }
                nav {
                    NavButton { label: "Find Best Buy", active: active_view() == View::BestBuy, onclick: move |_| active_view.set(View::BestBuy) }
                    NavButton { label: "Buy with Links", active: active_view() == View::BuyWithLinks, onclick: move |_| active_view.set(View::BuyWithLinks) }
                    NavButton { label: "Research", active: active_view() == View::Research, onclick: move |_| active_view.set(View::Research) }
                    NavButton { label: "Account Setup", active: active_view() == View::AccountSetup, onclick: move |_| active_view.set(View::AccountSetup) }
                }
                div { class: "sidebar_footer",
                    span { class: "badge", "{checkout_count} checkout link(s)" }
                    p { "{status}" }
                }
            }

            main { class: "content",
                match active_view() {
                    View::BestBuy => rsx! {
                        section { class: "workspace two_col",
                            div { class: "left",
                                div { class: "panel compact",
                                    div { class: "section_header",
                                        div {
                                            h2 { "Find Best Buy" }
                                            p { "Search in the installed phone app, then extract visible product rows for comparison." }
                                        }
                                    }
                                    div { class: "form_grid",
                                        label { "Device"
                                            select {
                                                value: "{selected_device_value}",
                                                onchange: move |event| selected_device.set(event.value()),
                                                option { value: "", "Select phone" }
                                                for device in device_rows.iter() {
                                                    option {
                                                        key: "{device}",
                                                        value: "{device}",
                                                        "{device}"
                                                    }
                                                }
                                            }
                                        }
                                        label { "Query"
                                            input {
                                                value: "{query}",
                                                placeholder: "pentel p205",
                                                oninput: move |event| query.set(event.value())
                                            }
                                        }
                                        label { "Budget min"
                                            input {
                                                value: "{budget_min}",
                                                placeholder: "RM",
                                                oninput: move |event| budget_min.set(event.value())
                                            }
                                        }
                                        label { "Budget max"
                                            input {
                                                value: "{budget_max}",
                                                placeholder: "RM",
                                                oninput: move |event| budget_max.set(event.value())
                                            }
                                        }
                                    }
                                    div { class: "toolbar",
                                        ToggleButton {
                                            label: "Shopee",
                                            active: include_shopee(),
                                            onclick: move |_| include_shopee.set(!include_shopee())
                                        }
                                        ToggleButton {
                                            label: "TikTok",
                                            active: include_tiktok(),
                                            onclick: move |_| include_tiktok.set(!include_tiktok())
                                        }
                                        ToggleButton {
                                            label: "Most relevant",
                                            active: result_group() == ResultGroup::MostRelevant,
                                            onclick: move |_| result_group.set(ResultGroup::MostRelevant)
                                        }
                                        ToggleButton {
                                            label: "Top sales",
                                            active: result_group() == ResultGroup::TopSales,
                                            onclick: move |_| result_group.set(ResultGroup::TopSales)
                                        }
                                    }
                                    div { class: "toolbar",
                                        button {
                                            onclick: move |_| {
                                                let text = query.read().trim().to_owned();
                                                if text.is_empty() {
                                                    status.set("Type a product query first.".to_owned());
                                                    return;
                                                }
                                                if !include_shopee() {
                                                    status.set("Only Shopee phone search is implemented right now. Enable Shopee.".to_owned());
                                                    return;
                                                }
                                                status.set(format!("Searching Shopee on phone: {text} ({})", result_group().label()));
                                                let mut args = vec![
                                                    "phone-best-buy".to_owned(),
                                                    text,
                                                    "--group".to_owned(),
                                                    result_group().backend_value().to_owned(),
                                                ];
                                                add_device_arg(&mut args, &selected_device());
                                                args.push("--json".to_owned());
                                                match run_backend_json_owned::<Vec<ProductSummary>>(args) {
                                                    Ok(rows) => {
                                                        selected_product.set(None);
                                                        products.set(rows);
                                                        if let Ok(shot) = run_backend_json_owned::<DeviceScreenshot>(phone_args("phone-screenshot", &selected_device())) {
                                                            screenshot.set(Some(shot));
                                                        }
                                                        status.set("Search complete. Select a row to inspect it.".to_owned());
                                                    }
                                                    Err(error) => status.set(error),
                                                }
                                            },
                                            "Search phone app"
                                        }
                                        button {
                                            onclick: move |_| refresh_phone(&mut device_status, &mut selected_device, &mut device_apps, &mut screenshot, &mut status),
                                            "Refresh phone"
                                        }
                                        button {
                                            onclick: move |_| {
                                                match run_backend_json_owned::<DeviceStatus>(phone_args("phone-optimize", &selected_device())) {
                                                    Ok(value) => {
                                                        let message = value.message.clone();
                                                        device_status.set(value);
                                                        status.set(message);
                                                    }
                                                    Err(error) => status.set(error),
                                                }
                                            },
                                            "Prepare phone"
                                        }
                                    }
                                }

                                div { class: "panel product_list",
                                    div { class: "section_header",
                                        div {
                                            h3 { "Results" }
                                            p { "{product_rows.len()} visible row(s) extracted from the phone UI" }
                                        }
                                    }
                                    if product_rows.is_empty() {
                                        EmptyState { text: "Search Shopee to render product rows here. The phone app remains the source of truth." }
                                    } else {
                                        div { class: "table",
                                            for (index, product) in product_rows.iter().enumerate() {
                                                div {
                                                    key: "{product.id}",
                                                    class: if selected_product() == Some(index) { "result_row selected" } else { "result_row" },
                                                    onclick: move |_| selected_product.set(Some(index)),
                                                    div {
                                                        span { class: "platform", "{product.platform}" }
                                                        span { class: "muted", "{product.result_group}" }
                                                    }
                                                    div { class: "title", "{product.title}" }
                                                    div { class: "facts",
                                                        span { "{product.price_label}" }
                                                        span { "{product.shipping_label}" }
                                                        span { "{product.rating_label}" }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }

                            div { class: "right",
                                PhonePanel {
                                    phone_message,
                                    phone_image,
                                    device_status: device_status.read().clone(),
                                    selected_device: selected_device(),
                                    app_rows,
                                    on_refresh: move |_| refresh_phone(&mut device_status, &mut selected_device, &mut device_apps, &mut screenshot, &mut status),
                                    on_swipe_up: move |_| run_phone_action(&mut status, "phone-swipe", &["160", "520", "160", "180"], &selected_device()),
                                    on_swipe_down: move |_| run_phone_action(&mut status, "phone-swipe", &["160", "180", "160", "520"], &selected_device()),
                                    on_tap_center: move |_| run_phone_action(&mut status, "phone-tap", &["160", "320"], &selected_device()),
                                }
                                ProductPane {
                                    product: current_product,
                                    on_add: move |url: String| {
                                        let mut links = checkout_links.read().clone();
                                        if !links.iter().any(|item| item == &url) {
                                            links.push(url);
                                            checkout_links.set(links);
                                        }
                                        active_view.set(View::BuyWithLinks);
                                    },
                                    on_research: move |title: String| {
                                        research_query.set(title);
                                        active_view.set(View::Research);
                                    }
                                }
                            }
                        }
                    },
                    View::BuyWithLinks => rsx! {
                        section { class: "workspace single",
                            div { class: "panel",
                                div { class: "section_header",
                                    div {
                                        h2 { "Buy with Links" }
                                        p { "This is the checkout staging area. Add links from Best Buy or paste links manually." }
                                    }
                                }
                                textarea {
                                    value: "{checkout_input}",
                                    placeholder: "Paste one or more Shopee/TikTok links, one per line.",
                                    oninput: move |event| checkout_input.set(event.value())
                                }
                                div { class: "toolbar",
                                    button {
                                        onclick: move |_| {
                                            let mut links = checkout_links.read().clone();
                                            for line in checkout_input.read().lines() {
                                                let value = line.trim();
                                                if !value.is_empty() && !links.iter().any(|item| item == value) {
                                                    links.push(value.to_owned());
                                                }
                                            }
                                            checkout_input.set(String::new());
                                            checkout_links.set(links);
                                        },
                                        "Add links"
                                    }
                                    button {
                                        onclick: move |_| {
                                            let links = checkout_links.read().clone();
                                            if links.is_empty() {
                                                status.set("Add at least one checkout link first.".to_owned());
                                                return;
                                            }
                                            let mut args = vec!["detect".to_owned()];
                                            args.extend(links);
                                            args.push("--json".to_owned());
                                            match run_backend_json_owned::<Vec<DetectedLink>>(args) {
                                                Ok(rows) => {
                                                    detected_links.set(rows);
                                                    status.set("Links detected.".to_owned());
                                                }
                                                Err(error) => status.set(error),
                                            }
                                        },
                                        "Detect links"
                                    }
                                    button {
                                        onclick: move |_| {
                                            let links = checkout_links.read().clone();
                                            if links.is_empty() {
                                                status.set("Add at least one checkout link first.".to_owned());
                                                return;
                                            }
                                            let mut args = vec!["checkout-plan".to_owned()];
                                            args.extend(links);
                                            args.push("--json".to_owned());
                                            match run_backend_json_owned::<CheckoutPlan>(args) {
                                                Ok(plan) => {
                                                    status.set("Checkout plan ready. Final payment stays user-controlled.".to_owned());
                                                    checkout_plan.set(Some(plan));
                                                }
                                                Err(error) => status.set(error),
                                            }
                                        },
                                        "Build checkout plan"
                                    }
                                    button {
                                        onclick: move |_| {
                                            checkout_links.set(Vec::new());
                                            detected_links.set(Vec::new());
                                            checkout_plan.set(None);
                                        },
                                        "Clear"
                                    }
                                }
                            }

                            div { class: "panel",
                                h3 { "Staged links ({checkout_count})" }
                                if checkout_count == 0 {
                                    EmptyState { text: "No checkout links yet. Add from Best Buy or paste links above." }
                                } else {
                                    for link in checkout_links.read().iter() {
                                        div { class: "link_row", key: "{link}", "{link}" }
                                    }
                                }
                            }

                            div { class: "panel",
                                h3 { "Detection and checkout handoff" }
                                for item in link_rows {
                                    div { class: "result_row",
                                        div {
                                            span { class: "platform", "{item.platform}" }
                                            span { class: if item.is_supported_for_mvp { "ok" } else { "warn" },
                                                if item.is_supported_for_mvp { "supported" } else { "limited" }
                                            }
                                        }
                                        div { class: "title", "{item.original_url}" }
                                        if item.product_identity.is_some() {
                                            p { class: "muted",
                                                "{identity_summary(item.product_identity.as_ref())}"
                                            }
                                        }
                                    }
                                }
                                if let Some(plan) = checkout_plan_value {
                                    div { class: "callout",
                                        h4 { "Checkout plan" }
                                        p { "Platform: {plan.platform} · Items: {plan.item_count}" }
                                        p { "URL: {plan.checkout_url}" }
                                        p { class: "muted", "Detected links: {plan.detected_links.len()}" }
                                        button {
                                            onclick: move |_| open_url(&plan.checkout_url),
                                            "Open checkout handoff"
                                        }
                                        for warning in plan.warnings {
                                            p { class: "warn", "{warning}" }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    View::Research => rsx! {
                        section { class: "workspace two_col",
                            div { class: "left",
                                div { class: "panel",
                                div { class: "section_header",
                                    div {
                                        h2 { "Research" }
                                        p { "Use this before checkout to reduce impulse buying and verify quality signals outside marketplace UI." }
                                    }
                                }
                                div { class: "search_line",
                                    input {
                                        value: "{research_query}",
                                        placeholder: "product name, model, or concern",
                                        oninput: move |event| research_query.set(event.value())
                                    }
                                    button {
                                        onclick: move |_| {
                                            let text = research_query.read().trim().to_owned();
                                            if text.is_empty() {
                                                status.set("Type a research query first.".to_owned());
                                                return;
                                            }
                                            let args = ["research".to_owned(), text, "--json".to_owned()];
                                            match run_backend_json_owned::<ResearchBrief>(args) {
                                                Ok(brief) => {
                                                    selected_youtube_video.set(None);
                                                    status.set(format!("Research complete: Ollama {}", brief.ollama_status));
                                                    research_brief.set(Some(brief));
                                                }
                                                Err(error) => status.set(error),
                                            }
                                        },
                                        "Research"
                                    }
                                }
                            }
                            if let Some(brief) = research_value {
                                div { class: "panel",
                                    h3 { "{brief.query}" }
                                    p { "{brief.overview}" }
                                    div { class: "callout ai_answer",
                                        h4 {
                                            if let Some(model) = brief.ollama_model.as_ref() {
                                                "Ollama response ({model})"
                                            } else {
                                                "Ollama response"
                                            }
                                        }
                                        if let Some(answer) = brief.ollama_response.as_ref() {
                                            p { "{answer}" }
                                        } else {
                                            p { class: "muted", "{brief.ollama_status}" }
                                        }
                                    }
                                    if let Some(overview) = brief.google_ai_overview {
                                        div { class: "callout",
                                            h4 { "Google AI Overview extraction" }
                                            p { "{overview}" }
                                        }
                                    }
                                    h4 { "Questions before buying" }
                                    for question in brief.key_questions {
                                        p { class: "bullet", "{question}" }
                                    }
                                    h4 { "Cautions" }
                                    for caution in brief.cautions {
                                        p { class: "warn", "{caution}" }
                                    }
                                    h4 { "Sources" }
                                    for source in brief.scraped_sources {
                                        SourceRow {
                                            key: "{source.url}",
                                            title: source.title,
                                            url: source.url,
                                            detail: format!("{} · {}", source.source_type, source.snippet),
                                            on_select: move |url: String| open_research_source(&url, None, &mut selected_youtube_video, &mut status),
                                        }
                                    }
                                    for link in brief.source_links {
                                        SourceRow {
                                            key: "{link}",
                                            title: link.clone(),
                                            url: link,
                                            detail: "Search source".to_owned(),
                                            on_select: move |url: String| open_research_source(&url, None, &mut selected_youtube_video, &mut status),
                                        }
                                    }
                                }
                            }
                            }
                            div { class: "right",
                                YoutubePanel { video: selected_youtube_value }
                            }
                        }
                    },
                    View::AccountSetup => rsx! {
                        section { class: "workspace single",
                            div { class: "panel",
                                div { class: "section_header",
                                    div {
                                        h2 { "Account Setup" }
                                        p { "Credentials are stored in the OS keyring. Login prompts, OTP, CAPTCHA, and payment remain supervised." }
                                    }
                                }
                                div { class: "toolbar",
                                    button {
                                        onclick: move |_| refresh_phone(&mut device_status, &mut selected_device, &mut device_apps, &mut screenshot, &mut status),
                                        "Refresh phone"
                                    }
                                    button {
                                        onclick: move |_| {
                                            match run_backend_json::<Vec<AccountSetupStatus>>(&["account-status", "--json"]) {
                                                Ok(rows) => account_statuses.set(rows),
                                                Err(error) => status.set(error),
                                            }
                                        },
                                        "Refresh accounts"
                                    }
                                }
                            }

                            div { class: "panel grid_2",
                                AccountCard {
                                    platform: "shopee",
                                    username: shopee_username(),
                                    password: shopee_password(),
                                    on_username: move |value: String| shopee_username.set(value),
                                    on_password: move |value: String| shopee_password.set(value),
                                    on_save: move |_| save_credentials("shopee", &mut shopee_username, &mut shopee_password, &mut account_statuses, &mut status),
                                    on_open: move |_| open_marketplace("shopee", &selected_device(), &mut status),
                                }
                                AccountCard {
                                    platform: "tiktok",
                                    username: tiktok_username(),
                                    password: tiktok_password(),
                                    on_username: move |value: String| tiktok_username.set(value),
                                    on_password: move |value: String| tiktok_password.set(value),
                                    on_save: move |_| save_credentials("tiktok", &mut tiktok_username, &mut tiktok_password, &mut account_statuses, &mut status),
                                    on_open: move |_| open_marketplace("tiktok", &selected_device(), &mut status),
                                }
                            }

                            div { class: "panel",
                                h3 { "Phone app readiness" }
                                for app in app_rows {
                                    div { class: "result_row", key: "{app.platform}",
                                        div {
                                            span { class: "platform", "{app.platform}" }
                                            span { class: if app.installed { "ok" } else { "warn" },
                                                if app.installed { "installed" } else { "missing" }
                                            }
                                        }
                                        p { class: "muted", "{app.package_name}" }
                                        p { "{app.message}" }
                                    }
                                }
                                div { class: "search_line",
                                    input {
                                        value: "{apk_path}",
                                        placeholder: "Optional local APK path",
                                        oninput: move |event| apk_path.set(event.value())
                                    }
                                    button {
                                        onclick: move |_| {
                                            let path = apk_path.read().trim().to_owned();
                                            if path.is_empty() {
                                                status.set("Enter an APK path first.".to_owned());
                                                return;
                                            }
                                            let mut args = vec!["phone-install-apk".to_owned(), path];
                                            add_device_arg(&mut args, &selected_device());
                                            args.push("--json".to_owned());
                                            match run_backend_json_owned::<DeviceStatus>(args) {
                                                Ok(value) => {
                                                    status.set(value.message.clone());
                                                    device_status.set(value);
                                                }
                                                Err(error) => status.set(error),
                                            }
                                        },
                                        "Install APK"
                                    }
                                }
                            }

                            div { class: "panel",
                                h3 { "Stored account state" }
                                for account in account_rows {
                                    div { class: "result_row", key: "{account.platform}",
                                        div {
                                            span { class: "platform", "{account.platform}" }
                                            span { class: if account.configured { "ok" } else { "warn" },
                                                if account.configured { "configured" } else { "not configured" }
                                            }
                                        }
                                        p { "{account.credential_storage}" }
                                        p { class: "muted", "{account.next_action}" }
                                    }
                                }
                            }
                        }
                    },
                }
            }
        }
    }
}

#[component]
fn YoutubePanel(video: Option<YoutubeVideo>) -> Element {
    rsx! {
        div { class: "panel youtube_panel",
            div { class: "section_header",
                div {
                    h3 { "Video source" }
                    if let Some(video) = video.as_ref() {
                        p { "{video.title}" }
                    } else {
                        p { "Select a YouTube source to watch it here." }
                    }
                }
            }
            if let Some(video) = video {
                div { class: "youtube_frame",
                    iframe {
                        src: "{youtube_embed_url(&video.id)}",
                        title: "YouTube player",
                        allow: "accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share",
                        allowfullscreen: true,
                    }
                }
                button { onclick: move |_| open_url(&video.source_url), "Open in browser" }
            } else {
                div { class: "youtube_placeholder",
                    div { class: "video_mark", "YT" }
                    p { "YouTube videos from Sources will load in this panel." }
                }
            }
        }
    }
}

#[component]
fn SourceRow(
    title: String,
    url: String,
    detail: String,
    on_select: EventHandler<String>,
) -> Element {
    rsx! {
        div { class: "source",
            button {
                onclick: {
                    let url = url.clone();
                    move |_| on_select.call(url.clone())
                },
                "Open"
            }
            div {
                div { class: "title", "{title}" }
                p { class: "muted", "{detail}" }
                button {
                    class: "source_url_text",
                    onclick: {
                        let url = url.clone();
                        move |_| on_select.call(url.clone())
                    },
                    "{url}"
                }
            }
        }
    }
}

#[component]
fn NavButton(label: &'static str, active: bool, onclick: EventHandler<MouseEvent>) -> Element {
    rsx! {
        button {
            class: if active { "nav_button active" } else { "nav_button" },
            onclick: move |event| onclick.call(event),
            "{label}"
        }
    }
}

#[component]
fn ToggleButton(label: &'static str, active: bool, onclick: EventHandler<MouseEvent>) -> Element {
    rsx! {
        button {
            class: if active { "toggle active" } else { "toggle" },
            onclick: move |event| onclick.call(event),
            "{label}"
        }
    }
}

#[component]
fn EmptyState(text: &'static str) -> Element {
    rsx! {
        div { class: "empty", "{text}" }
    }
}

#[component]
fn PhonePanel(
    phone_message: String,
    phone_image: Option<String>,
    device_status: DeviceStatus,
    selected_device: String,
    app_rows: Vec<DeviceAppStatus>,
    on_refresh: EventHandler<MouseEvent>,
    on_swipe_up: EventHandler<MouseEvent>,
    on_swipe_down: EventHandler<MouseEvent>,
    on_tap_center: EventHandler<MouseEvent>,
) -> Element {
    let adb_label = device_status
        .adb_path
        .clone()
        .unwrap_or_else(|| "not found".to_owned());
    let scrcpy_label = device_status
        .scrcpy_path
        .clone()
        .unwrap_or_else(|| "optional".to_owned());
    let devices_label = if device_status.devices.is_empty() {
        "none".to_owned()
    } else {
        device_status.devices.join(", ")
    };

    rsx! {
        div { class: "panel phone_panel",
            div { class: "section_header",
                div {
                    h3 { "Physical phone" }
                    p { "{phone_message}" }
                }
                span { class: if device_status.ready { "ok" } else { "warn" },
                    if device_status.ready { "ready" } else { "not ready" }
                }
            }
            div { class: "phone_frame",
                if let Some(path) = phone_image {
                    img { src: "{path}" }
                } else {
                    div { class: "phone_placeholder", "No screenshot yet" }
                }
            }
            div { class: "toolbar small",
                button { onclick: move |event| on_refresh.call(event), "Screenshot" }
                button { onclick: move |event| on_tap_center.call(event), "Tap center" }
                button { onclick: move |event| on_swipe_up.call(event), "Swipe up" }
                button { onclick: move |event| on_swipe_down.call(event), "Swipe down" }
            }
            p { class: "muted", "ADB: {adb_label}" }
            p { class: "muted", "scrcpy: {scrcpy_label}" }
            p { class: "muted", "Devices: {devices_label}" }
            p { class: "muted", "Selected: {selected_device}" }
            for app in app_rows {
                div { class: "mini_row", key: "{app.platform}",
                    span { "{app.platform}" }
                    span { class: if app.installed { "ok" } else { "warn" },
                        if app.installed { "installed" } else { "missing" }
                    }
                }
            }
        }
    }
}

#[component]
fn ProductPane(
    product: Option<ProductSummary>,
    on_add: EventHandler<String>,
    on_research: EventHandler<String>,
) -> Element {
    rsx! {
        div { class: "panel detail",
            h3 { "Single pane details" }
            if let Some(product) = product {
                div { class: "hero_title", "{product.title}" }
                div { class: "toolbar small",
                    span { class: "platform", "{product.platform}" }
                    span { class: "badge", "{product.data_status}" }
                }
                div { class: "detail_grid",
                    Detail { label: "Price", value: product.price_label.clone() }
                    Detail { label: "Shipping", value: product.shipping_label.clone() }
                    Detail { label: "Reviews", value: product.rating_label.clone() }
                    Detail { label: "Stock", value: product.stock_label.clone() }
                    Detail { label: "Seller", value: product.seller_label.clone() }
                    Detail { label: "Group", value: product.result_group.clone() }
                }
                h4 { "Decision notes" }
                if product.risk_notes.is_empty() {
                    p { class: "muted", "No extra notes extracted yet. Verify options, vouchers, seller, and final shipping in the phone app." }
                } else {
                    for note in product.risk_notes {
                        p { class: "warn", "{note}" }
                    }
                }
                div { class: "toolbar",
                    button {
                        onclick: {
                            let url = product.product_url.clone();
                            move |_| on_add.call(url.clone())
                        },
                        "Add to checkout links"
                    }
                    button {
                        onclick: {
                            let title = product
                                .research_queries
                                .first()
                                .cloned()
                                .unwrap_or_else(|| product.title.clone());
                            move |_| on_research.call(title.clone())
                        },
                        "Research this"
                    }
                    button {
                        onclick: {
                            let url = product.product_url.clone();
                            move |_| open_url(&url)
                        },
                        "Open Shopee"
                    }
                }
            } else {
                EmptyState { text: "Select a product after searching. This pane keeps the important decision data in one readable place." }
            }
        }
    }
}

#[component]
fn Detail(label: &'static str, value: String) -> Element {
    rsx! {
        div { class: "detail_item",
            span { "{label}" }
            strong { "{value}" }
        }
    }
}

#[component]
fn AccountCard(
    platform: &'static str,
    username: String,
    password: String,
    on_username: EventHandler<String>,
    on_password: EventHandler<String>,
    on_save: EventHandler<MouseEvent>,
    on_open: EventHandler<MouseEvent>,
) -> Element {
    rsx! {
        div { class: "account_card",
            h3 { "{platform}" }
            input {
                value: "{username}",
                placeholder: "username / email / phone",
                oninput: move |event| on_username.call(event.value())
            }
            input {
                r#type: "password",
                value: "{password}",
                placeholder: "password",
                oninput: move |event| on_password.call(event.value())
            }
            div { class: "toolbar small",
                button { onclick: move |event| on_save.call(event), "Save credentials" }
                button { onclick: move |event| on_open.call(event), "Open app" }
            }
        }
    }
}

fn refresh_phone(
    device_status: &mut Signal<DeviceStatus>,
    selected_device: &mut Signal<String>,
    device_apps: &mut Signal<Vec<DeviceAppStatus>>,
    screenshot: &mut Signal<Option<DeviceScreenshot>>,
    status: &mut Signal<String>,
) {
    match run_backend_json_owned::<DeviceStatus>(phone_args("phone-status", &selected_device())) {
        Ok(value) => {
            if selected_device.read().is_empty() && value.devices.len() == 1 {
                selected_device.set(value.devices[0].clone());
            }
            status.set(value.message.clone());
            device_status.set(value);
        }
        Err(error) => status.set(error),
    }
    if let Ok(rows) =
        run_backend_json_owned::<Vec<DeviceAppStatus>>(phone_args("phone-apps", &selected_device()))
    {
        device_apps.set(rows);
    }
    if let Ok(shot) = run_backend_json_owned::<DeviceScreenshot>(phone_args(
        "phone-screenshot",
        &selected_device(),
    )) {
        screenshot.set(Some(shot));
    }
}

fn run_phone_action(status: &mut Signal<String>, command: &str, values: &[&str], device: &str) {
    let mut args = vec![command.to_owned()];
    args.extend(values.iter().map(|value| value.to_string()));
    add_device_arg(&mut args, device);
    args.push("--json".to_owned());
    match run_backend_json_owned::<DeviceStatus>(args) {
        Ok(value) => status.set(value.message),
        Err(error) => status.set(error),
    }
}

fn save_credentials(
    platform: &str,
    username: &mut Signal<String>,
    password: &mut Signal<String>,
    account_statuses: &mut Signal<Vec<AccountSetupStatus>>,
    status: &mut Signal<String>,
) {
    let username_value = username.read().trim().to_owned();
    let password_value = password.read().to_owned();
    if username_value.is_empty() || password_value.is_empty() {
        status.set(format!("{platform}: username and password are required."));
        return;
    }

    let args = [
        "account-set".to_owned(),
        platform.to_owned(),
        "--username".to_owned(),
        username_value,
        "--password".to_owned(),
        password_value,
        "--json".to_owned(),
    ];

    match run_backend_json_owned::<AccountSetupStatus>(args) {
        Ok(saved) => {
            password.set(String::new());
            status.set(format!("{platform}: credentials saved in OS keyring."));
            let mut rows = account_statuses.read().clone();
            rows.retain(|row| row.platform != saved.platform);
            rows.push(saved);
            account_statuses.set(rows);
        }
        Err(error) => status.set(error),
    }
}

fn open_marketplace(platform: &str, device: &str, status: &mut Signal<String>) {
    let mut args = vec!["phone-open-app".to_owned(), platform.to_owned()];
    add_device_arg(&mut args, device);
    args.push("--json".to_owned());
    match run_backend_json_owned::<DeviceStatus>(args) {
        Ok(value) => status.set(value.message),
        Err(error) => status.set(error),
    }
}

fn open_research_source(
    url: &str,
    title: Option<&str>,
    selected_youtube_video: &mut Signal<Option<YoutubeVideo>>,
    status: &mut Signal<String>,
) {
    let trimmed = url.trim();
    if trimmed.is_empty() {
        status.set("Source URL is empty.".to_owned());
        return;
    }

    if let Some(id) = youtube_video_id(trimmed) {
        selected_youtube_video.set(Some(YoutubeVideo {
            id,
            title: title.unwrap_or(trimmed).to_owned(),
            source_url: trimmed.to_owned(),
        }));
        status.set("Loaded YouTube source in the video panel.".to_owned());
        return;
    }

    if !is_http_url(trimmed) {
        status.set("Source URL is invalid or unsupported.".to_owned());
        return;
    }

    open_url(trimmed);
    status.set("Opened source in your default browser.".to_owned());
}

fn is_http_url(url: &str) -> bool {
    url.starts_with("https://") || url.starts_with("http://")
}

fn youtube_video_id(url: &str) -> Option<String> {
    let trimmed = url.trim();
    if trimmed.is_empty() {
        return None;
    }

    if let Some(rest) = trimmed.split("youtu.be/").nth(1) {
        return clean_youtube_id(rest);
    }
    if let Some(rest) = trimmed.split("/embed/").nth(1) {
        return clean_youtube_id(rest);
    }
    if let Some(rest) = trimmed.split("watch?").nth(1) {
        for part in rest.split('&') {
            if let Some(value) = part.strip_prefix("v=") {
                return clean_youtube_id(value);
            }
        }
    }

    None
}

fn clean_youtube_id(value: &str) -> Option<String> {
    let id = value
        .split(['?', '&', '/', '#'])
        .next()
        .unwrap_or("")
        .trim();
    if id.len() == 11
        && id
            .chars()
            .all(|ch| ch.is_ascii_alphanumeric() || ch == '-' || ch == '_')
    {
        Some(id.to_owned())
    } else {
        None
    }
}

fn youtube_embed_url(video_id: &str) -> String {
    format!("https://www.youtube.com/embed/{video_id}")
}

fn phone_args(command: &str, device: &str) -> Vec<String> {
    let mut args = vec![command.to_owned()];
    add_device_arg(&mut args, device);
    args.push("--json".to_owned());
    args
}

fn add_device_arg(args: &mut Vec<String>, device: &str) {
    let trimmed = device.trim();
    if !trimmed.is_empty() {
        args.push("--device".to_owned());
        args.push(trimmed.to_owned());
    }
}

fn identity_summary(identity: Option<&ProductIdentity>) -> String {
    let Some(identity) = identity else {
        return "No parsed product identity".to_owned();
    };

    format!(
        "shop={} item={} slug={} platform={}",
        identity.shop_id.as_deref().unwrap_or("-"),
        identity.item_id.as_deref().unwrap_or("-"),
        identity.raw_slug.as_deref().unwrap_or("-"),
        identity.platform
    )
}

fn run_backend_json<T: DeserializeOwned>(args: &[&str]) -> Result<T, String> {
    run_backend_json_owned(
        args.iter()
            .map(|value| value.to_string())
            .collect::<Vec<_>>(),
    )
}

fn run_backend_json_owned<T: DeserializeOwned>(
    args: impl IntoIterator<Item = String>,
) -> Result<T, String> {
    let output = backend_output(args)?;
    if output.status.success() {
        serde_json::from_slice::<T>(&output.stdout).map_err(|error| {
            format!(
                "Backend returned invalid JSON: {error}. Output: {}",
                String::from_utf8_lossy(&output.stdout)
            )
        })
    } else {
        Err(String::from_utf8_lossy(&output.stderr).trim().to_owned())
    }
}

fn backend_output(args: impl IntoIterator<Item = String>) -> Result<Output, String> {
    let mut command = Command::new("uv");
    command.arg("run").arg("oss-my");
    for arg in args {
        command.arg(arg);
    }
    command
        .output()
        .map_err(|error| format!("Failed to run backend through uv: {error}"))
}

fn open_url(url: &str) {
    if url.trim().is_empty() {
        return;
    }

    #[cfg(target_os = "windows")]
    let _ = Command::new("cmd").args(["/C", "start", "", url]).spawn();

    #[cfg(target_os = "macos")]
    let _ = Command::new("open").arg(url).spawn();

    #[cfg(all(unix, not(target_os = "macos")))]
    let _ = Command::new("xdg-open").arg(url).spawn();
}

fn path_to_file_url(path: &str) -> String {
    let normalized = Path::new(path).to_string_lossy().replace('\\', "/");
    if normalized.starts_with('/') {
        format!("file://{normalized}")
    } else {
        format!("file:///{normalized}")
    }
}

#[cfg(test)]
mod tests {
    use super::youtube_video_id;

    #[test]
    fn extracts_youtube_watch_video_id() {
        assert_eq!(
            youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            Some("dQw4w9WgXcQ".to_owned())
        );
    }

    #[test]
    fn extracts_youtu_be_video_id() {
        assert_eq!(
            youtube_video_id("https://youtu.be/dQw4w9WgXcQ?t=42"),
            Some("dQw4w9WgXcQ".to_owned())
        );
    }

    #[test]
    fn extracts_youtube_embed_video_id() {
        assert_eq!(
            youtube_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ"),
            Some("dQw4w9WgXcQ".to_owned())
        );
    }

    #[test]
    fn rejects_malformed_youtube_video_id() {
        assert_eq!(youtube_video_id("https://youtu.be/not-valid"), None);
    }
}

const APP_CSS: &str = r#"
:root {
    background: #0c0f14;
    color: #d9dee7;
    font-family: Inter, Segoe UI, system-ui, sans-serif;
}

body {
    margin: 0;
}

button,
input,
select,
textarea {
    font: inherit;
}

button {
    border: 1px solid #2b3340;
    border-radius: 10px;
    background: #161b23;
    color: #d9dee7;
    padding: 9px 12px;
    cursor: pointer;
}

button:hover {
    border-color: #60708a;
    background: #1c2430;
}

input,
select,
textarea {
    box-sizing: border-box;
    width: 100%;
    border: 1px solid #26303d;
    border-radius: 10px;
    background: #0e131a;
    color: #e9edf5;
    padding: 10px 12px;
    outline: none;
}

textarea {
    min-height: 120px;
    resize: vertical;
}

label {
    display: grid;
    gap: 6px;
    color: #98a3b3;
    font-size: 12px;
}

.app {
    display: grid;
    grid-template-columns: 260px 1fr;
    min-height: 100vh;
}

.sidebar {
    border-right: 1px solid #202631;
    background: #0a0d12;
    padding: 18px;
    display: flex;
    flex-direction: column;
    gap: 18px;
}

.brand {
    display: flex;
    gap: 12px;
    align-items: center;
}

.brand_mark {
    display: grid;
    place-items: center;
    width: 42px;
    height: 42px;
    border-radius: 12px;
    background: #f97316;
    color: #111;
    font-weight: 800;
}

h1,
h2,
h3,
h4,
p {
    margin: 0;
}

h1 {
    font-size: 16px;
}

h2 {
    font-size: 22px;
}

h3 {
    font-size: 16px;
}

h4 {
    font-size: 13px;
    color: #cdd6e3;
}

p {
    color: #98a3b3;
    line-height: 1.45;
}

nav {
    display: grid;
    gap: 8px;
}

.nav_button {
    text-align: left;
    background: transparent;
}

.nav_button.active,
.toggle.active {
    background: #243042;
    border-color: #6b7f9d;
}

.sidebar_footer {
    margin-top: auto;
    display: grid;
    gap: 8px;
}

.content {
    padding: 18px;
    overflow: auto;
}

.workspace {
    display: grid;
    gap: 14px;
}

.two_col {
    grid-template-columns: minmax(520px, 1fr) 380px;
    align-items: start;
}

.single {
    max-width: 980px;
}

.left,
.right {
    display: grid;
    gap: 14px;
}

.panel {
    border: 1px solid #202936;
    border-radius: 16px;
    background: #10151d;
    padding: 16px;
    display: grid;
    gap: 14px;
}

.compact {
    gap: 12px;
}

.section_header {
    display: flex;
    justify-content: space-between;
    gap: 16px;
    align-items: start;
}

.form_grid {
    display: grid;
    grid-template-columns: 180px 1fr 120px 120px;
    gap: 10px;
}

.toolbar,
.search_line {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
}

.search_line input {
    flex: 1;
    min-width: 260px;
}

.small button,
.small span {
    font-size: 12px;
    padding: 7px 9px;
}

.product_list {
    max-height: calc(100vh - 255px);
    overflow: auto;
}

.table {
    display: grid;
    gap: 8px;
}

.result_row,
.link_row,
.source {
    border: 1px solid #202936;
    border-radius: 12px;
    background: #0d1219;
    padding: 12px;
    display: grid;
    gap: 7px;
}

.source {
    grid-template-columns: auto 1fr;
}

.source_link_button {
    text-align: left;
}

.source_url_text {
    width: fit-content;
    border: 0;
    background: transparent;
    color: #9fc3ff;
    padding: 0;
    text-align: left;
    font-size: 12px;
}

.source_url_text:hover {
    background: transparent;
    color: #c5dbff;
    text-decoration: underline;
}

.youtube_panel {
    position: sticky;
    top: 18px;
}

.youtube_frame {
    aspect-ratio: 16 / 9;
    border: 1px solid #252e3a;
    border-radius: 12px;
    background: #06080c;
    overflow: hidden;
}

.youtube_frame iframe {
    width: 100%;
    height: 100%;
    border: 0;
}

.youtube_placeholder {
    min-height: 260px;
    border: 1px dashed #2a3442;
    border-radius: 12px;
    background: #0b1322;
    display: grid;
    place-items: center;
    gap: 10px;
    padding: 24px;
    text-align: center;
}

.video_mark {
    display: grid;
    place-items: center;
    width: 56px;
    height: 56px;
    border-radius: 12px;
    background: #162033;
    color: #9fc3ff;
    font-weight: 800;
}

.result_row {
    cursor: pointer;
}

.result_row.selected {
    border-color: #f97316;
    background: #18130e;
}

.title,
.hero_title {
    color: #edf1f7;
    font-weight: 650;
}

.hero_title {
    font-size: 19px;
    line-height: 1.3;
}

.facts {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    color: #98a3b3;
    font-size: 12px;
}

.platform,
.badge,
.ok,
.warn {
    display: inline-flex;
    width: fit-content;
    border-radius: 999px;
    padding: 3px 8px;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .05em;
}

.platform {
    background: #162033;
    color: #9fc3ff;
}

.badge {
    background: #1d2430;
    color: #cdd6e3;
}

.ok {
    background: #10261b;
    color: #80e6a1;
}

.warn {
    background: #301b12;
    color: #ffad7a;
}

.phone_panel {
    gap: 12px;
}

.phone_frame {
    border: 1px solid #252e3a;
    border-radius: 18px;
    background: #06080c;
    min-height: 330px;
    overflow: hidden;
    display: grid;
    place-items: center;
}

.phone_frame img {
    width: 100%;
    max-height: 430px;
    object-fit: contain;
}

.phone_placeholder,
.empty {
    color: #6f7a8a;
    border: 1px dashed #2a3442;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
}

.mini_row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    color: #98a3b3;
}

.detail_grid,
.grid_2 {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
}

.detail_item,
.account_card,
.callout {
    border: 1px solid #202936;
    border-radius: 12px;
    background: #0d1219;
    padding: 12px;
    display: grid;
    gap: 7px;
}

.ai_answer p {
    color: #d9dee7;
    white-space: pre-wrap;
}

.detail_item span,
.muted {
    color: #98a3b3;
    font-size: 12px;
}

.detail_item strong {
    color: #edf1f7;
    font-size: 13px;
}

.bullet::before {
    content: "• ";
    color: #f97316;
}
"#;
