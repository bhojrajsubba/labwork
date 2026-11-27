require_relative "boot"
require "rails"
require "action_controller/railtie"
require "action_view/railtie"

module NovaVault
  class Application < Rails::Application
    config.load_defaults 7.1
    config.eager_load = false
    config.secret_key_base = ENV.fetch("SECRET_KEY", "lab_secret_key_change_in_production_123456")

    # Allow requests from any Cloudflare domain, localhost, or Docker hostname
    config.hosts.clear

    # Serve /static/style.css from public/static/
    config.public_file_server.enabled = true

    # Send logs to STDOUT for Docker visibility
    logger = ActiveSupport::Logger.new($stdout)
    logger.formatter = ::Logger::Formatter.new
    config.logger = ActiveSupport::TaggedLogging.new(logger)
    config.log_level = :info

    config.session_store :cookie_store, key: "_novavault_session"

    mode = ENV.fetch("MODE", "vulnerable").downcase
    if mode == "vulnerable"
      # Prevent Rack::ETag from injecting `Cache-Control: max-age=0, private, must-revalidate`
      config.middleware.delete Rack::ETag
    end
  end
end
