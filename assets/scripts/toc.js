(function () {
  const toc = document.querySelector("[data-toc]");
  if (!toc) return;

  const headings = Array.from(document.querySelectorAll("main h2, main h3"))
    .filter((heading) => !heading.closest("[data-toc]"));
  if (!headings.length) return;

  const list = document.createElement("ol");
  headings.forEach((heading, index) => {
    if (!heading.id) {
      heading.id = `section-${index + 1}`;
    }
    const item = document.createElement("li");
    const link = document.createElement("a");
    link.href = `#${heading.id}`;
    link.textContent = heading.textContent;
    item.appendChild(link);
    list.appendChild(item);
  });

  toc.appendChild(list);
})();
