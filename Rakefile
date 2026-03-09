require "html-proofer"

task default: [:test]

desc "Build the Jekyll site"
task :build do
  require "jekyll"
  Jekyll::Commands::Build.process({})
end

desc "Run html-proofer on the built site"
task test: :build do
  options = {
    checks: ["Links", "Images", "Scripts"],
    allow_hash_href: true,
    ignore_urls: [
      /linkedin\.com/,
      /twitter\.com/,
      /x\.com/,
      /facebook\.com/,
      /archive\.org/,
      /amzn\.to/,
      /syddanger\.ca/,
      /etcsl\.orinst\.ox\.ac\.uk/,
      /transtorah\.org/,
      /sefaria\.org/,
      /thepinknews\.com/,
      /intomore\.com/,
      /newsweek\.com/,
    ],
    ignore_status_codes: [403, 429, 999],
    swap_urls: {
      "^/$" => "/index.html",
    },
    disable_external: ENV.fetch("DISABLE_EXTERNAL", "true") == "true",
    enforce_https: false,
  }
  HTMLProofer.check_directory("./_site", options).run
end

desc "Run html-proofer including external link checks (slower)"
task :test_external do
  ENV["DISABLE_EXTERNAL"] = "false"
  Rake::Task[:test].invoke
end
