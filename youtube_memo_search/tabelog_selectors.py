from __future__ import annotations


TABELOG_SELECTORS = {
    "area_inputs": [
        "input[name='sa']",
        "input[placeholder*='エリア']",
        "input[aria-label*='エリア']",
        "input[type='search'][name*='area']",
    ],
    "keyword_inputs": [
        "input[name='sk']",
        "input[name='sw']",
        "input[placeholder*='キーワード']",
        "input[placeholder*='ジャンル']",
        "input[aria-label*='キーワード']",
    ],
    "budget_selects": [
        "select[name='LstCosT']",
        "#lstcost-sidebar",
        "select[name='LstCos']",
        "#lstcos-sidebar",
        "select[name*='budget']",
        "select[name*='price']",
        "select[id*='budget']",
        "select[id*='price']",
    ],
    "max_budget_selects": [
        "select[name='LstCosT']",
        "#lstcost-sidebar",
    ],
    "budget_buttons": [
        "button[aria-label*='予算']",
        "button[data-testid*='budget']",
        "button[class*='budget']",
    ],
    "search_buttons": [
        "button[type='submit']",
        "input[type='submit']",
        "button[aria-label*='検索']",
        "button[class*='search']",
    ],
}
