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

    # Serve /static/style.css from public/static/ with public Cache-Control headers
    config.public_file_server.enabled = true
    config.public_file_server.headers = {
      "Cache-Control" => "public, max-age=86400"
    }

    # Send logs to STDOUT for Docker visibility
    logger = ActiveSupport::Logger.new($stdout)
    logger.formatter = ::Logger::Formatter.new
    config.logger = ActiveSupport::TaggedLogging.new(logger)
    config.log_level = :info

    config.session_store :cookie_store, key: "_novavault_session"

    mode = ENV.fetch("MODE", "vulnerable").downcase
    if mode == "vulnerable"
      # Keep responses neutral (do not inject Rails' default `private` Cache-Control)
      require "rack/etag"
      config.middleware.delete Rack::ETag
      require "action_dispatch/middleware/flash"
      config.middleware.delete ActionDispatch::Flash

      strip_default_cc = Class.new do
        def initialize(app)
          @app = app
        end

        def call(env)
          status, headers, body = @app.call(env)
          cc_key = headers.keys.find { |k| k.casecmp?("cache-control") }
          if cc_key && headers[cc_key] == "max-age=0, private, must-revalidate"
            headers.delete(cc_key)
          end
          [status, headers, body]
        end
      end
      config.middleware.insert_before 0, strip_default_cc
    end
  end
end
