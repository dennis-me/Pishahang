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

require 'addressable/uri'
require 'pp'
require 'json'

# This Class is the Class of Sonata Aws Repository
class SonataAwsRepository < Sinatra::Application
  @@awsr_schema = JSON.parse(JSON.dump(YAML.load(open('https://raw.githubusercontent.com/tobiasdierich/son-schema/master/complex-service-record/cosr-schema.yml') { |f| f.read })))
  # https and openssl libs (require 'net/https' require 'openssl') enable access to external https links behind a proxy

  DEFAULT_OFFSET = '0'
  DEFAULT_LIMIT = '10'
  DEFAULT_MAX_LIMIT = '100'

  # @method get_root
  # @overload get '/'
  get '/' do
    headers 'Content-Type' => 'text/plain; charset=utf8'
    halt 200, interfaces_list.to_yaml
  end

  # @method get_aws-instances
  # @overload get "/aws-instances"
  # Gets all aws-instances
  get '/aws-instances' do
    uri = Addressable::URI.new
    params['offset'] ||= DEFAULT_OFFSET
    params['limit'] ||= DEFAULT_LIMIT
    uri.query_values = params
    logger.info "awsr: entered GET /records/awsr/aws-instances?#{uri.query}"

    # transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    # Get paginated list
    headers = { 'Accept' => 'application/json', 'Content-Type' => 'application/json' }
    headers[:params] = params unless params.empty?
    # get rid of :offset and :limit
    [:offset, :limit].each { |k| keyed_params.delete(k) }
    valid_fields = [:page]
    logger.info "awsr: keyed_params.keys - valid_fields = #{keyed_params.keys - valid_fields}"
    json_error 400, "awsr: wrong parameters #{params}" unless keyed_params.keys - valid_fields == []

    requests = Awsr.paginate(page: params[:page], limit: params[:limit])
    logger.info "awsr: leaving GET /requests?#{uri.query} with #{requests.to_json}"
    halt 200, requests.to_json if requests
    json_error 404, 'csr: No requests were found'

    begin
      # Get paginated list
      awsr_json = @awsr.to_json
      if content_type == 'application/json'
        return 200, awsr_json
      elsif content_type == 'application/x-yaml'
        headers 'Content-Type' => 'text/plain; charset=utf8'
        awsr_yml = json_to_yaml(awsr_json)
        return 200, awsr_yml
      end
    rescue
      logger.error 'Error Establishing a Database Connection'
      return 500, 'Error Establishing a Database Connection'
    end
  end

  # @method get_aws-instances
  # @overload get "/aws-instances"
  # Gets aws-instances with an id
  get '/aws-instances/:id' do
    begin
      @awsinstance = Awsr.find(params[:id])
    rescue Mongoid::Errors::DocumentNotFound => e
      halt(404)
    end
    awsr_json = @awsinstance.to_json
    return 200, awsr_json
  end

  # @method post_aws-instances
  # @overload post "/aws-instances"
  # Post a new aws-instances information
  post '/aws-instances' do
    return 415 unless request.content_type == 'application/json'
    # Validate JSON format
    instance, errors = parse_json(request.body.read)
    awsr_json = instance
    return 400, errors.to_json if errors
    # Validation against schema
    errors = validate_json(awsr_json, @@awsr_schema)

    puts 'awsr: ', Awsr.to_json
    return 422, errors.to_json if errors

    begin
      instance = Awsr.find({ '_id' => instance['_id'] })
      return 409, 'ERROR: Duplicated awsr UUID'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    begin
      instance = Awsr.create!(instance)
    rescue Moped::Errors::OperationFailure => e
      return 409, 'ERROR: Duplicated awsr UUID'
    end
    return 200, instance.to_json
  end

  # @method put_aws-instances
  # @overload put "/aws-instances"
  # Puts a aws-instances record
  put '/aws-instances/:id' do
    # Return if content-type is invalid
    415 unless request.content_type == 'application/json'
    # Validate JSON format
    instance, errors = parse_json(request.body.read)
    return 400, errors.to_json if errors
    # Retrieve stored version
    new_awsr = instance

    # Validation against schema
    errors = validate_json(new_awsr, @@awsr_schema)

    puts 'awsr: ', Awsr.to_json
    return 422, errors.to_json if errors

    begin
      awsr = Awsr.find_by('_id' => params[:id])
      puts 'awsr is found'
    rescue Mongoid::Errors::DocumentNotFound => e
      return 404, 'csr not found'
    end

    # Update to new version
    puts 'Updating...'
    begin
      # Delete old record
      Awsr.where('_id' => params[:id]).delete
      # Create a record
      new_awsr = Awsr.create!(instance)
    rescue Moped::Errors::OperationFailure => e
      return 409, 'ERROR: Duplicated awsr UUID'
    end

    awsr_json = new_awsr.to_json
    return 200, awsr_json
  end

  delete '/aws-instances/:id' do
    # Return if content-type is invalid
    begin
      awsr = Awsr.find_by('_id' => params[:id])
      puts 'awsr is found'
    rescue Mongoid::Errors::DocumentNotFound => e
      return 404, 'awsr not found'
    end

    # Delete the awsr
    puts 'Deleting...'
    begin
      # Delete the aws service record
      Awsr.where('_id' => params[:id]).delete
    end

    return 200
  end
end
