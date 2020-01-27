##
## Copyright (c) 2015 SONATA-NFV
## ALL RIGHTS RESERVED.
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##
## Neither the name of the SONATA-NFV
## nor the names of its contributors may be used to endorse or promote
## products derived from this software without specific prior written
## permission.
##
## This work has been performed in the framework of the SONATA project,
## funded by the European Commission under Grant number 671517 through
## the Horizon 2020 and 5G-PPP programmes. The authors would like to
## acknowledge the contributions of their colleagues of the SONATA
## partner consortium (www.sonata-nfv.eu).

# @see FPGARepository
class SonataFpgaRepository < Sinatra::Application

  @@fpgar_schema=JSON.parse(JSON.dump(YAML.load(open('https://raw.githubusercontent.com/dennis-me/Pishahang/blob/fpga-service/son-schema/fpga-service-record/fpgar-schema.yml'){|f| f.read})))
  # https and openssl libs (require 'net/https' require 'openssl') enable access to external https links behind a proxy

  before do
    # Gatekeepr authn. code will go here for future implementation
    # --> Gatekeeper authn. disabled

    if settings.environment == 'development'
      return
    end
    #authorized?
  end

  # @method get_root
  # @overload get '/'
  # Get all available interfaces
  # -> Get all interfaces
  get '/' do
    headers 'Content-Type' => 'text/plain; charset=utf8'
    halt 200, interfaces_list.to_yaml
  end

  # @method get_log
  # @overload get '/fpga-instances/log'
  #	Returns contents of log file
  # Management method to get log file of repository remotely
  get '/fpga-instances/log' do
    filename = 'log/development.log'

    # For testing purposes only
    begin
      txt = open(filename)

    rescue => err
      logger.error "Error reading log file: #{err}"
      return 500, "Error reading log file: #{err}"
    end

    return 200, txt.read.to_s
  end

  # @method get_fpga
  # @overload get '/fpga-instances'
  #	Returns a list of FPGARs
  # List all FPGARs in JSON or YAML
  #   - JSON (default)
  #   - YAML including output parameter (e.g /fpga-instances?output=YAML)
  get '/fpga-instances' do
    params[:offset] ||= 1
    params[:limit] ||= 10

    # Only accept positive numbers
    params[:offset] = 1 if params[:offset].to_i < 1
    params[:limit] = 2 if params[:limit].to_i < 1

    # Get paginated list
    fps = Fpsr.paginate(page: params[:offset], limit: params[:limit])
    logger.debug(fps)
    # Build HTTP Link Header
    headers['Link'] = build_http_link(params[:offset].to_i, params[:limit])

    if params[:output] == 'YAML'
      content_type = 'application/x-yaml'
    else
      content_type = 'application/json'
    end

    begin
      # Get paginated list
      fps = Fpsr.paginate(page: params[:offset], limit: params[:limit])
      logger.debug(fps)
      # Build HTTP Link Header
      headers['Link'] = build_http_link(params[:offset].to_i, params[:limit])
      fps_json = fps.to_json
      if content_type == 'application/json'
        return 200, fps_json
      elsif content_type == 'application/x-yaml'
        fps_yml = json_to_yaml(fps_json)
        return 200, fps_yml
      end
    rescue
      logger.error 'Error Establishing a Database Connection'
      return 500, 'Error Establishing a Database Connection'
    end
  end

  # @method get_fpgainstances
  # @overload get "/fpga-instances"
  # Gets fpgas-instances with an id
  # Return JSON or YAML
  #   - JSON (default)
  #   - YAML including output parameter (e.g /fpga-instances?output=YAML)
  get '/fpga-instances/:id' do
    begin
      @fpsInstance = Fpsr.find(params[:id])
    rescue Mongoid::Errors::DocumentNotFound => e
      halt (404)
    end

    if params[:output] == 'YAML'
      content_type = 'application/x-yaml'
    else
      content_type = 'application/json'
    end
    fps_json = @fpsInstance.to_json
    if content_type == 'application/json'
      return 200, fps_json
    elsif content_type == 'application/x-yaml'
      fps_yml = json_to_yaml(fps_json)
      return 200, fps_yml
    end
  end

  # @method post_fpgars
  # @overload post '/fpga-instances'
  # Post a FPGA in YAML format
  # @param [YAML/JSON]
  # Post a fpgar
  # Return JSON or YAML depending on content_type
  post '/fpga-instances' do

    if request.content_type ==  'application/json'
      instance, errors = parse_json(request.body.read)
      return 400, errors.to_json if errors
      fps_json = instance
    elsif request.content_type == 'application/x-yaml'
      instance, errors = parse_yaml(request.body.read)
      return 400, errors.to_json if errors
      fps_json = yaml_to_json(instance)
      instance, errors = parse_json(fps_json)
      return 400, errors.to_json if errors
    end
    puts 'fpga: ', Fpsr.to_json
    errors = validate_json(fps_json,@@fpgar_schema)
    return 422, errors.to_json if errors

    begin
      instance = Fpsr.find( instance['id'] )
      return 409, 'ERROR: Duplicated FPGA ID'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    # Save to DB
    begin
      instance = Fpsr.create!(instance)
    rescue Moped::Errors::OperationFailure => e
      return 409, 'ERROR: Duplicated FPGA ID' if e.message.include? 'E11000'
    end

    puts 'New FPGA has been added'
    fps_json = instance.to_json
    if request.content_type == 'application/json'
      return 200, fps_json
    elsif request.content_type == 'application/x-yaml'
      fps_yml = json_to_yaml(fps_json)
      return 200, fps_yml
    end
  end

  # @method put_fpgars
  # @overload put '/fpga-instances'
  # Put a FPGA in YAML format
  # @param [JSON/YAML]
  # Put a fpgar
  # Return JSON or YAML depending on content_type
  put '/fpga-instances/:id' do

    if request.content_type ==  'application/json'
      instance, errors = parse_json(request.body.read)
      return 400, errors.to_json if errors
      fps_json = instance
    elsif request.content_type == 'application/x-yaml'
      instance, errors = parse_yaml(request.body.read)
      return 400, errors.to_json if errors
      fps_json = yaml_to_json(instance)
      instance, errors = parse_json(fps_json)
      return 400, errors.to_json if errors
    end

    begin
      fpgar = Fpsr.find(params[:id])
      puts 'FPGA is found'
    rescue Mongoid::Errors::DocumentNotFound => e
      return 404, 'This FPGAR does not exists'
    end

    puts 'validating entry: ', fps_json
    errors = validate_json(fps_json,@@fpgar_schema)
    return 422, errors.to_json if errors

    # Update to new version
    puts 'Updating...'
    begin
      # Delete old record
      Fpsr.where( {'id' => params[:id] }).delete
      # Create a record
      new_fpgar = Fpsr.create!(instance)
    rescue Moped::Errors::OperationFailure => e
      return 409, 'ERROR: Duplicated FPGA ID' if e.message.include? 'E11000'
    end

    puts 'New FPGA has been updated'
    fps_json = instance.to_json
    if request.content_type == 'application/json'
      return 200, fps_json
    elsif request.content_type == 'application/x-yaml'
      fps_yml = json_to_yaml(fps_json)
      return 200, fps_yml
    end
  end

  # @method delete_fpgar_external_fpga_id
  # @overload delete '/fpga-instances/:id'
  #	Delete a fpga by its ID
  #	@param [Integer] external_fpga_id fpga external ID
  # Delete a fpga
  delete '/fpga-instances/:id' do
    begin
      fpga = Fpsr.find_by( {'id' =>  params[:id]})
    rescue Mongoid::Errors::DocumentNotFound => e
      return 404,'ERROR: Operation failed'
    end
    fpga.destroy
    return 200, 'OK: fpgar removed'
  end
end