#!/usr/bin/env python3
"""LAL!ROLE ひみつのアトリエ: data/core.json から docs/ に静的サイトを生成する。
（つくりは「寺田てら ないしょのお寺」~/tera-naisho と同じ流れ。MV はないので、絵は本人の X ポストの埋め込みで見せる）

- data/core.json … 年表。1 行 1 できごとの JSON。
  {date: "YYYY" | "YYYY-MM" | "YYYY-MM-DD", cat, title, note, big, x}
  cat: game（ゲーム）/ book（本の表紙）/ vtuber（VTuber・ライブ）/ exhibit（展示）/ milestone（できごと）
  x … 本人（@Laxxxli）が公式のお仕事を告知したポスト。告知のないお仕事は載せない（同人誌・個人の絵は対象外）。
- これからの予定 … ~/knowledge-os/oshi-events.js の artist が LAL!ROLE の行を docs/upcoming.js に書き出す。
- 画像 … LAL!ROLE さんの絵の画像ファイルは置かない。本人が無断転載・無断使用を禁止しているため（2022-08-29 のポスト）、
  絵は X の公式埋め込みだけで表示する。AI 画像も置かない。
非公式のファンサイト。アフィリエイト・広告は入れない。
"""
import html, json, os, re, shutil
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "docs")
NAME = "LAL!ROLE ひみつのアトリエ"
SITE = "https://lalrole-atelier.github.io/"
GA = "G-EHWF25C1RB"  # ほかのサイトと共通の測定 ID（GA4 でホスト名 lalrole-atelier.github.io で絞る）
EVENTS_JS = os.path.expanduser("~/knowledge-os/oshi-events.js")
TODAY = date.today().isoformat()
ME = "https://x.com/Laxxxli"

CATS = {
    "game": ("ゲーム", "#2f7fd8"),
    "book": ("本の表紙", "#d0567a"),
    "vtuber": ("VTuber・ライブ", "#7a5bd6"),
    "exhibit": ("展示", "#169a8c"),
    "milestone": ("できごと", "#64748b"),
}
CAT_PAGES = [("game", "ゲーム", {"game"}, "アークナイツ、アズールレーン、maimai。あなたが遊んだゲームの、あのキャラクターに会えます。"),
             ("books", "本の表紙", {"book"}, "書店で手に取ったあの一冊の表紙を、もう一度たどれます。カバー・季節の表紙・店頭 POP まで。"),
             ("vtuber", "VTuber・ライブ", {"vtuber"}, "推しのアルバムやライブのビジュアルを、描いた人の目線でたどれます。"),
             ("exhibit", "展示・できごと", {"exhibit", "milestone"}, "展示・受賞・インタビューなど、お仕事のまわりのできごとです。")]

esc = html.escape
T = sorted((json.loads(l.strip().rstrip(",")) for l in open(os.path.join(ROOT, "data", "core.json"), encoding="utf-8") if l.strip().startswith("{")),
           key=lambda e: e["date"])
YEARS = sorted({e["date"][:4] for e in T})
CSS = open(os.path.join(ROOT, "assets", "base.css"), encoding="utf-8").read()


def fmt(d):
    p = d.split("-")
    s = p[0] + "年"
    if len(p) > 1:
        s += str(int(p[1])) + "月"
    if len(p) > 2:
        s += str(int(p[2])) + "日"
    return s


def x_embed(url):
    """本人の告知ポストを X の公式埋め込みで表示する（絵はここで見える。画像ファイルは置かない）"""
    if not url:
        return ""
    return (f'<div class="xpost"><blockquote class="twitter-tweet" data-lang="ja" data-dnt="true" data-conversation="none">'
            f'<a href="{url}">LAL!ROLE さんの X ポストを見る</a></blockquote></div>')


X_SCRIPT = '<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>'


def item(e):
    name, color = CATS.get(e["cat"], ("その他", "#64748b"))
    note = f'<p>{esc(e["note"])}</p>' if e.get("note") else ""
    note += x_embed(e.get("x"))
    return (f'<li class="ev{" big" if e.get("big") else ""}"><div class="dt">{fmt(e["date"])}</div>'
            f'<div class="bd"><span class="chip" style="--c:{color}">{name}</span>'
            f'<h3>{esc(e["title"])}</h3>{note}</div></li>')


def year_stats(y):
    ev = [e for e in T if e["date"][:4] == y]
    parts = [(CATS[k][0], sum(1 for e in ev if e["cat"] == k)) for k in ("game", "book", "vtuber", "exhibit")]
    return " ／ ".join(f"{a} {n} 件" for a, n in parts if n)


def timeline(events, by_year=True):
    if not events:
        return '<p class="empty">まだ記録がありません。</p>'
    out, cur = [], None
    for e in events:
        y = e["date"][:4]
        if by_year and y != cur:
            if cur:
                out.append("</ol>")
            st = year_stats(y)
            out.append(f'<h2 class="yr" id="y{y}"><a href="{{R}}year/{y}.html">{y}年</a> <small class="ys">{sum(1 for x in T if x["date"][:4] == y)} のお仕事・できごと{"（" + st + "）" if st else ""}</small></h2><ol class="tl">')
            cur = y
        out.append(item(e))
    out.append("</ol>")
    if not by_year:
        out.insert(0, '<ol class="tl">')
    return "\n".join(out)


NAV = [("index.html", "アトリエの入口"), ("timeline.html", "全部の年表"), ("game.html", "ゲーム"), ("books.html", "本の表紙"),
       ("vtuber.html", "VTuber・ライブ"), ("exhibit.html", "展示・できごと"), ("schedule.html", "これからの予定"), ("about.html", "このアトリエについて")]


def sidebar():
    years = "".join(f'<li><a href="{{R}}year/{y}.html">{y}年</a></li>' for y in YEARS)
    cats = "".join(f'<li><a href="{{R}}{k}.html">{t}（{sum(1 for e in T if e["cat"] in c)}）</a></li>' for k, t, c, _ in CAT_PAGES)
    return f"""<aside class="side">
<div class="box"><h2>🎨 このアトリエについて</h2><p class="note">イラストレーター・LAL!ROLE（らりろーる）さんが公式に発表したお仕事を、本人の告知ポストと一緒に年表でたどれる<b>非公式</b>のファンサイトです。ご本人・公式とは関係ありません。</p></div>
<div class="box"><h2>🗂 お仕事の種類でたどる</h2><ul>{cats}</ul></div>
<div class="box sticky"><h2>📅 年でたどる</h2><ul>{years}</ul>
<h2 style="margin-top:14px">📣 公式はこちら</h2><ul>
<li><a href="{ME}" rel="noopener" target="_blank">LAL!ROLE さんの X（@Laxxxli）</a></li>
<li><a href="https://bsky.app/profile/laxxxli.bsky.social" rel="noopener" target="_blank">LAL!ROLE さんの Bluesky</a></li></ul></div>
</aside>"""


def ga_tag():
    return (f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA}"></script>'
            f"<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','{GA}');</script>")


def page(path, title, desc, body, crumb=None, hero=False):
    R = "../" * path.count("/")
    nav = "".join(f'<li><a href="{R}{h}"{" class=on" if h == path else ""}>{t}</a></li>' for h, t in NAV)
    cr = '<div class="crumb"><a href="' + R + 'index.html">アトリエの入口</a> › ' + " › ".join(crumb) + "</div>" if crumb else ""
    full = NAME if path == "index.html" else f"{title}｜{NAME}"
    heroh = f'<div class="hero">{hero}</div>' if hero else ""
    widgets = X_SCRIPT if "twitter-tweet" in body else ""
    doc = f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(full)}</title><meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}{'' if path == 'index.html' else path}">
<meta property="og:title" content="{esc(full)}"><meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website"><meta property="og:url" content="{SITE}{path}"><meta name="twitter:card" content="summary">
{ga_tag()}
<style>{CSS}</style></head><body class="{"home" if path == "index.html" else "sub"}">
<header class="top"><div class="in"><a class="logo" href="{R}index.html">LAL!ROLE <span>ひみつの</span>アトリエ</a><span class="badge">非公式ファンサイト</span></div></header>
<nav class="gnav"><ul>{nav}</ul></nav>
{heroh}
<div class="layout"><main>{cr}{body}</main>{sidebar()}</div>
<footer>{NAME} は、LAL!ROLE さんを応援するファンによる<b>非公式</b>のファンサイトです。LAL!ROLE さんご本人・関係する企業や団体とは関係ありません。<br>
掲載情報は、本人の X での告知と、各社の公式発表をもとにしています。最新・正確な情報は<a href="{ME}" target="_blank" rel="noopener">本人の X</a>でご確認ください。<br>
LAL!ROLE さんの絵の複製・転載はしていません。絵は X の公式埋め込みで表示しています（権利は各権利者に帰属します）。 ／ <a href="{R}about.html">このアトリエについて・プライバシー</a><br>最終更新: {TODAY}</footer>
{widgets}</body></html>"""
    doc = doc.replace("{R}", R)
    p = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(doc)
    PAGES.append(path)


def upcoming_box(limit, title="これからの予定", more=True):
    link = '<p style="margin:10px 0 0;text-align:right"><a href="{R}schedule.html">予定をもっと見る →</a></p>' if more else ""
    return f"""<section><h2 class="sec-t">{title}</h2>
<ul class="up" id="up" data-limit="{limit}"><li class="empty">読み込み中…</li></ul>{link}
<p class="notice" style="margin-top:12px">予定は公式発表をもとに毎週まとめています。変わることがあるので、公式の最新情報もあわせてご確認ください。</p></section>
<script src="{{R}}upcoming.js"></script><script>
(function(){{var el=document.getElementById('up'),lim=+el.dataset.limit,t=new Date(),pad=function(n){{return('0'+n).slice(-2)}},
today=t.getFullYear()+'-'+pad(t.getMonth()+1)+'-'+pad(t.getDate()),K={{live:'ライブ',release:'発売',tieup:'コラボ',event:'イベント',media:'配信',ticket:'チケット'}},
W='日月火水木金土',it=(window.LAL_UPCOMING||[]).filter(function(e){{return e.date>=today}}).slice(0,lim);
if(!it.length){{el.innerHTML='<li class="empty">いま分かっている予定はありません。</li>';return}}
el.innerHTML=it.map(function(e){{var d=new Date(e.date+'T00:00:00');return '<li><div class="d">'+(d.getMonth()+1)+'/'+d.getDate()+'<small>'+d.getFullYear()+'（'+W[d.getDay()]+'）</small></div><div><span class="k">'+(K[e.kind]||'')+'</span><div>'+e.title.replace(/[<>&]/g,'')+'</div></div></li>'}}).join('')}})();
</script>"""


def write_upcoming():
    items = []
    if os.path.exists(EVENTS_JS):
        s = open(EVENTS_JS, encoding="utf-8").read()
        for m in re.finditer(r'\{\s*date:\s*"([\d-]+)",\s*artist:\s*"LAL!ROLE",\s*title:\s*"((?:[^"\\]|\\.)*)",\s*kind:\s*"(\w+)"', s):
            if m.group(3) != "anniv" and "要確認" not in m.group(2):
                items.append({"date": m.group(1), "title": json.loads('"' + m.group(2) + '"'), "kind": m.group(3)})
    items.sort(key=lambda e: e["date"])
    open(os.path.join(OUT, "upcoming.js"), "w", encoding="utf-8").write("window.LAL_UPCOMING=" + json.dumps(items, ensure_ascii=False) + ";\n")
    return len(items)


def build():
    if os.path.exists(OUT):
        for n in os.listdir(OUT):
            p = os.path.join(OUT, n)
            shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
    os.makedirs(OUT, exist_ok=True)
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    n_up = write_upcoming()
    work = [e for e in T if e["cat"] != "milestone"]
    n = {k: sum(1 for e in T if e["cat"] == k) for k in CATS}

    # お仕事のあしあと（年ごとのお仕事の数）
    ys = [str(y) for y in range(int(YEARS[0]), int(YEARS[-1]) + 1)]
    cnt = {y: sum(1 for e in work if e["date"][:4] == y) for y in ys}
    mx = max(cnt.values()) or 1
    cols = "".join(f'<a class="bar" href="{{R}}year/{y}.html" title="{y}年: {cnt[y]} 件"><span style="--h:{cnt[y] / mx * 100:.0f}%"><b>{cnt[y]}</b></span><i>{y[2:]}</i></a>'
                   if cnt[y] else f'<span class="bar"><span style="--h:0%"></span><i>{y[2:]}</i></span>' for y in ys)
    activity = (f'<section><h2 class="sec-t">お仕事のあしあと</h2><p class="lead" style="margin-bottom:12px">本人が告知したお仕事 {len(work)} 件を、年ごとに数えました。棒を押すと、その年のページが開きます。</p>'
                f'<div class="bars" role="img" aria-label="{ys[0]}年から{ys[-1]}年までの年ごとのお仕事の数">{cols}</div></section>')
    recent = [e for e in T if e["date"] <= TODAY][-4:][::-1]
    cat_cards = "".join(f'<a class="cc" href="{{R}}{k}.html" style="--c:{CATS[sorted(c)[0]][1]}"><b>{t}</b><span>{sum(1 for e in T if e["cat"] in c)} 件</span><small>{esc(l)}</small></a>' for k, t, c, l in CAT_PAGES)
    body = f"""<section><h1>ようこそ、ひみつのアトリエへ。</h1>
<p class="lead">来てくださって、ありがとうございます。ここでは、イラストレーター・LAL!ROLE（らりろーる）さんが公式に発表したお仕事を、あなたが好きなときにたどれます。『アークナイツ』のオーロラやラ・プルマ、EN 版『アズールレーン』3 周年のキービジュアル、『桜のような僕の恋人』の表紙、白上フブキさんのアルバムやライブのビジュアル、そしてにじさんじ『VSせめよん』まで。キャラクターに負けない密度の背景と、白昼夢のような光と水の表現で、たくさんの作品を彩ってきた LAL!ROLE さんと、一緒に作品をつくってきた皆さんへの拍手を込めて、ファンがまとめた非公式のアトリエです。絵はどれも、本人の告知ポストの埋め込みで見られます。</p>
<div class="stats"><div><b>{n["game"]}</b>ゲーム</div><div><b>{n["book"]}</b>本の表紙</div><div><b>{n["vtuber"]}</b>VTuber・ライブ</div><div><b>{YEARS[0]}〜</b>年から</div></div>
<p class="lead" style="margin-top:12px">あなたが LAL!ROLE さんの絵に出会ったのは、どの作品ですか？</p></section>
<section><h2 class="sec-t">最近のお仕事</h2>{timeline(recent, by_year=False)}
<p style="margin:6px 0 0;text-align:right"><a href="{{R}}timeline.html">全部の年表を見る →</a></p></section>
{activity}
<section><h2 class="sec-t">お仕事の種類でたどる</h2><div class="ccs">{cat_cards}</div></section>
{upcoming_box(5)}"""
    hdr = f'<div class="htxt"><b>{esc(NAME)}</b><p>イラストレーター LAL!ROLE さんの公式のお仕事を、本人の告知ポストと一緒に年表でたどれる非公式ファンサイトです。毎月書き足しています。</p></div>'
    page("index.html", NAME, f"イラストレーター LAL!ROLE（らりろーる）さんが公式に発表したお仕事 {len(work)} 件を、本人の告知ポストと一緒に年表でたどれる非公式ファンサイト。毎月更新。", body, hero=hdr)

    jump = " ".join(f'<a href="#y{y}">{y}</a>' for y in YEARS)
    page("timeline.html", "全部の年表", "LAL!ROLE さんの公式のお仕事を、最初の本の表紙から最新のビジュアルまで、すべて時系列で。",
         f'<section><h1>全部の年表</h1><p class="lead">LAL!ROLE さんのお仕事を、最初から通してたどれます。色のついた印は特に大きなお仕事です。絵は本人の告知ポストの埋め込みで表示されます。 年へジャンプ: {jump}</p></section><section>{timeline(T)}</section>',
         crumb=["全部の年表"])

    for i, y in enumerate(YEARS):
        ev = [x for x in T if x["date"][:4] == y]
        pv = f'<a href="{YEARS[i-1]}.html">← {YEARS[i-1]}年</a>' if i else "<span></span>"
        nx = f'<a href="{YEARS[i+1]}.html">{YEARS[i+1]}年 →</a>' if i + 1 < len(YEARS) else "<span></span>"
        page(f"year/{y}.html", f"{y}年の LAL!ROLE", f"{y}年の LAL!ROLE さんのお仕事・できごと（{len(ev)}件）を年表で。",
             f'<section><h1>{y}年の LAL!ROLE</h1><p class="lead">{len(ev)} のお仕事・できごと</p><p class="ys2">{year_stats(y)}</p></section>'
             f'<section>{timeline(ev, by_year=False)}<div class="pager">{pv}{nx}</div></section>', crumb=[f"{y}年"])

    for k, t, cats, lead in CAT_PAGES:
        ev = [x for x in T if x["cat"] in cats]
        page(f"{k}.html", t, f"LAL!ROLE さんの{t}のお仕事の年表。{lead}",
             f'<section><h1>{t}</h1><p class="lead">{lead}</p></section><section>{timeline(ev)}</section>', crumb=[t])

    page("schedule.html", "これからの予定", "LAL!ROLE さんのこれからのお仕事・グッズ発売などの予定。毎週更新。",
         '<section><h1>これからの予定</h1><p class="lead">次に LAL!ROLE さんの絵に会える日が、ひと目でわかります。</p></section>'
         + upcoming_box(80, "予定一覧", more=False), crumb=["これからの予定"])

    page("about.html", "このアトリエについて", "LAL!ROLE ひみつのアトリエについて、運営方針とプライバシーポリシー。", f"""<section><h1>このアトリエについて</h1>
<p>「LAL!ROLE ひみつのアトリエ」は、イラストレーター・LAL!ROLE（らりろーる）さんが公式に発表したお仕事を、ファンのあなたが好きなときにたどれるようにつくった<b>非公式</b>のファンサイトです。LAL!ROLE さんご本人、関係する企業・団体とは一切関係ありません。</p></section><section>
<h2>このアトリエでやっていること</h2><ul>
<li>本人の X（@Laxxxli）で告知された、ゲーム・本の表紙・VTuber のビジュアルなどの公式のお仕事を、年表にまとめています</li>
<li>紹介文は、告知と各社の公式発表をもとに、運営者が自分の言葉で書いています</li>
<li>毎月、新しいお仕事を書き足します。まちがいに気づいたときは直します</li></ul>
<h2>やらないこと</h2><ul>
<li>広告・アフィリエイトは載せません</li>
<li>LAL!ROLE さんの絵の複製・転載はしません。本人がすべての作品の無断転載・無断使用を禁止しているためです。絵は、本人の X ポストを X の公式埋め込みで表示しているだけで、画像ファイルはこのサイトに置いていません。権利は各権利者に帰属します</li>
<li>同人誌や個人の作品、ご本人の私生活に関することは載せません</li></ul>
<h2>AI の使い方と、お問い合わせ</h2>
<p>年表・紹介文の下書きにAIを使い、内容は運営者が本人の告知と公式の発表で確かめています。AI で作った絵は置いていません。</p>
<p>削除のご依頼や誤りのご指摘は、<a href="https://x.com/masabee1029" target="_blank" rel="noopener">X @masabee1029</a> の DM（ダイレクトメッセージ）でお知らせください。すぐに対応します。</p>
<h2>来てくださって、ありがとうございます</h2>
<p>たくさんのキャラクターと物語に光を当ててきた LAL!ROLE さん、一緒に作品をつくってきた作家・ゲーム・配信者の皆さん、そして応援を続けるファンの皆さんに、心から感謝しています。このアトリエが、あなたの「好き」をもう一度たしかめる場所になればうれしいです。</p>
<p>あなたのいちばん好きな LAL!ROLE さんのお仕事は、どれですか？</p>
<h2>プライバシーポリシー</h2>
<p>X のポストは X（旧 Twitter）の公式埋め込みで表示しているため、X が Cookie などで情報を取得する場合があります。アクセスの傾向を知るために Google アナリティクスを使っています。Cookie を使って匿名のアクセス情報を集めますが、個人を特定する情報は集めません。ブラウザの設定で Cookie を無効にできます。</p>
<h2>参考にしている情報源</h2><ul>
<li><a href="{ME}" target="_blank" rel="noopener">LAL!ROLE さん本人の X（@Laxxxli）</a></li>
<li>各作品の公式 X（アークナイツ・各出版社・各著者・にじさんじ・ChroNoiR など）</li>
<li><a href="https://ichi-up.net/cs2018/160" target="_blank" rel="noopener">1UP クリエイターセレクション vol.161 - LAL!ROLE</a></li></ul></section>""", crumb=["このアトリエについて"])

    sm = "".join(f"<url><loc>{SITE}{'' if p == 'index.html' else p}</loc><lastmod>{TODAY}</lastmod></url>" for p in PAGES)
    open(os.path.join(OUT, "sitemap.xml"), "w").write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {SITE}sitemap.xml\n")
    open(os.path.join(OUT, "404.html"), "w", encoding="utf-8").write(open(os.path.join(OUT, "index.html"), encoding="utf-8").read())
    print(f"built {len(PAGES)} pages, {len(T)} timeline events, {n_up} upcoming")


PAGES = []
if __name__ == "__main__":
    build()
