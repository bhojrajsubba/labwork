require "net/http"
require "json"
require "uri"

class VaultController < ApplicationController
  BOT_SERVICE_URL = ENV.fetch("BOT_SERVICE_URL", "http://wcd05-bot:5001/visit")

  def index
  end

  def login_form
  end

  def login
    username = params[:username].to_s.strip
    password = params[:password].to_s

    if USERS.key?(username) && USERS[username][:password] == password
      session[:user] = username
      # Avoid flash[] on login success so GET /profile does not emit Set-Cookie
      redirect_to "/profile"
    else
      @error_message = "Invalid username or password."
      render :login_form, status: :unauthorized
    end
  end

  def logout
    reset_session
    redirect_to "/login"
  end

  def profile
    unless current_user
      redirect_to "/login"
      return
    end

    if lab_mode == "secure"
      response.headers["Cache-Control"] = "no-store, no-cache, private, must-revalidate"
      response.headers["Pragma"] = "no-cache"
      response.headers["Expires"] = "0"
    else
      # Do not commit/re-write Set-Cookie on read-only profile views
      request.session_options[:skip] = true
    end

    render :profile
  end

  def report_form
  end

  def report
    target_path = params[:url].to_s.strip
    if target_path.empty?
      @alert_type = "danger"
      @alert_message = "Please enter a valid URL or path."
      render :report_form
      return
    end

    payload = { path: target_path }
    public_base = detect_public_base_url
    payload[:base_url] = public_base if public_base

    begin
      uri = URI.parse(BOT_SERVICE_URL)
      http = Net::HTTP.new(uri.host, uri.port)
      http.open_timeout = 5
      http.read_timeout = 15
      req = Net::HTTP::Post.new(uri.request_uri, "Content-Type" => "application/json")
      req.body = payload.to_json
      bot_resp = http.request(req)

      if bot_resp.code.to_i == 200
        @alert_type = "success"
        @alert_message = "Inspection request logged! Infrastructure Director (Dr. Alex Mercer) reviewed your link."
      else
        @alert_type = "warning"
        @alert_message = "Support bot encountered an error: #{bot_resp.body}"
      end
    rescue => e
      @alert_type = "danger"
      @alert_message = "Failed to reach support bot: #{e.message}"
    end

    render :report_form
  end

  private

  def detect_public_base_url
    host = request.host_with_port.to_s
    hostname = request.host.to_s.downcase
    return nil if ["127.0.0.1", "localhost", "wcd05-origin", "wcd05-app", ""].include?(hostname)

    proto = request.headers["X-Forwarded-Proto"].to_s.split(",").first.to_s.strip.downcase
    proto = "http" unless ["http", "https"].include?(proto)

    cf_visitor = request.headers["CF-Visitor"].to_s
    if !cf_visitor.empty?
      begin
        parsed = JSON.parse(cf_visitor)
        proto = parsed["scheme"] if ["http", "https"].include?(parsed["scheme"])
      rescue JSON::ParserError
      end
    end

    "#{proto}://#{host}"
  end
end
