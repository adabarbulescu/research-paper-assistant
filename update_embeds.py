
with open('utils/embeds.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('from models.paper import Paper', 'from models.paper import Paper\nfrom models.saved_paper import SavedPaper')
content = content.replace('entries: list[dict],', 'entries: list[SavedPaper],')
content = content.replace('paper = entry["paper"]', 'paper = entry.paper')
content = content.replace('saved_at = format_saved_date(entry.get("saved_at", ""))', 'saved_at = format_saved_date(entry.saved_at)')
content = content.replace('status = entry.get("status", "to-read")', 'status = entry.status')
content = content.replace('note = entry.get("note")', 'note = entry.note')
content = content.replace('def build_collection_embed(collection_name: str, papers: list[dict]) -> discord.Embed:', 'def build_collection_embed(collection_name: str, papers: list[SavedPaper]) -> discord.Embed:')

collection_loop = """    for idx, row in enumerate(papers[:15], start=1):
        raw_authors = row.get("authors", "")
        authors_list = (
            raw_authors
            if isinstance(raw_authors, list)
            else decode_str_list(raw_authors)
        )
        authors = format_authors(authors_list, limit=2)
        status = row.get("status", "to-read")
        s_emoji = status_emoji.get(status, "")
        published = (row.get("published") or "")[:10] or "Unknown"

        value_lines = [
            f"{s_emoji} **{status}**  •  {authors}  •  {published}",
            f"`{row['paper_id']}`  •  [📄 arXiv]({row['arxiv_url']})",
        ]
        if row.get("pdf_url"):
            value_lines[-1] += f"  •  [📥 PDF]({row['pdf_url']})"

        embed.add_field(
            name=f"`{idx}` {truncate(row.get('title', 'Untitled'), 200)}",
            value="\\n".join(value_lines),
            inline=False,
        )"""

new_collection_loop = """    for idx, sp in enumerate(papers[:15], start=1):
        authors = format_authors(sp.paper.authors, limit=2)
        status = sp.status
        s_emoji = status_emoji.get(status, "")
        published = sp.paper.published_date[:10] or "Unknown"

        value_lines = [
            f"{s_emoji} **{status}**  •  {authors}  •  {published}",
            f"`{sp.paper.arxiv_id}`  •  [📄 arXiv]({sp.paper.arxiv_url})",
        ]
        if sp.paper.pdf_url:
            value_lines[-1] += f"  •  [📥 PDF]({sp.paper.pdf_url})"

        embed.add_field(
            name=f"`{idx}` {truncate(sp.paper.title, 200)}",
            value="\\n".join(value_lines),
            inline=False,
        )"""

content = content.replace(collection_loop, new_collection_loop)

with open('utils/embeds.py', 'w', encoding='utf-8') as f:
    f.write(content)
