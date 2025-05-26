# Set working directory to the book source
setwd("user-guide")

# Render the book
bookdown::render_book("index.Rmd", output_format = "bookdown::gitbook")

# Back to the repo root
setwd("..")

# Add all changes and commit (source + _book)
system('git add -A')
system('git commit -m "Update book"')

# Push latest source changes
system('git push')

# Push _book/ to gh-pages
system('git subtree push --prefix user-guide/_book origin gh-pages')
