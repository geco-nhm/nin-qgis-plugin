# Set working directory to the book source
setwd("user-guide")

# In setup chunk
is_compressed <- FALSE

# Render the book (HTML GitBook version)
bookdown::render_book("index.Rmd", output_format = "bookdown::gitbook")

# Render the book (PDF version)
bookdown::render_book("index.Rmd", output_format = "bookdown::pdf_book", output_dir = "../../")

# In setup chunk
is_compressed <- TRUE

# Render the book in lower resolution (PDF version)
bookdown::render_book("index.Rmd", output_format = "bookdown::pdf_book", output_dir = "C:/Users/adamen/OneDrive - Universitetet i Oslo/documents/qgis_test")

# Back to the repo root
setwd("..")

# Add all changes and commit (source + _book)
system('git add -A')
system('git commit -m "Update book"')

# Push latest source changes
system('git push')

# Push _book/ to gh-pages
system('git subtree push --prefix user-guide/_book origin gh-pages')
