# Renders the user guide and publishes it to the gh-pages branch.
#
#   Rscript scripts/publish_book.R          (run from the repository root)
#
# The rendered book (docs/user-guide/_book) is not tracked on master. It is copied
# into a temporary worktree of the gh-pages branch and pushed from there.
# Set NIN_GUIDE_PDF_DIR to also render the PDF versions into that folder.

repo_root <- normalizePath(getwd(), winslash = "/")
if (!file.exists(file.path(repo_root, "docs", "user-guide", "index.Rmd"))) {
  stop("Run this script from the repository root.")
}

git <- function(...) {
  status <- system2("git", c(...))
  if (status != 0) stop("git ", paste(c(...), collapse = " "), " failed")
}

# Render the book (HTML GitBook version)
setwd(file.path(repo_root, "docs", "user-guide"))
is_compressed <- FALSE
bookdown::render_book("index.Rmd", output_format = "bookdown::gitbook")

# Render the PDF versions (optional)
pdf_dir <- Sys.getenv("NIN_GUIDE_PDF_DIR")
if (nzchar(pdf_dir)) {
  bookdown::render_book("index.Rmd", output_format = "bookdown::pdf_book",
                        output_dir = file.path(pdf_dir, "full"))
  # Lower resolution
  is_compressed <- TRUE
  bookdown::render_book("index.Rmd", output_format = "bookdown::pdf_book",
                        output_dir = file.path(pdf_dir, "compressed"))
}
setwd(repo_root)

# Copy _book into a worktree of gh-pages and push
book_dir <- file.path(repo_root, "docs", "user-guide", "_book")
worktree <- file.path(tempdir(), "nin-gh-pages")
git("fetch", "origin", "gh-pages")
git("worktree", "add", "--force", "-B", "gh-pages", shQuote(worktree), "origin/gh-pages")

old_files <- setdiff(list.files(worktree, all.files = TRUE, no.. = TRUE), ".git")
unlink(file.path(worktree, old_files), recursive = TRUE)
new_files <- list.files(book_dir, all.files = TRUE, no.. = TRUE, full.names = TRUE)
new_files <- new_files[basename(new_files) != "book.pdf"]
file.copy(new_files, worktree, recursive = TRUE)

git("-C", shQuote(worktree), "add", "-A")
if (system2("git", c("-C", shQuote(worktree), "diff", "--cached", "--quiet")) != 0) {
  git("-C", shQuote(worktree), "commit", "-m", shQuote("Update book"))
  git("-C", shQuote(worktree), "push", "origin", "gh-pages")
} else {
  message("The published book is already up to date.")
}
git("worktree", "remove", "--force", shQuote(worktree))
