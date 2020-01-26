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

# @see SonCatalogue
# class SonataCatalogue < Sinatra::Application

class CatalogueV2 < SonataCatalogue
  ### AWSD API METHODS ###

  # @method get_nssSS
  # @overload get '/catalogues/aws-services/?'
  #	Returns a list of AWSs
  # -> List many descriptors
  get '/aws-services/?' do
    params['offset'] ||= DEFAULT_OFFSET
    params['limit'] ||= DEFAULT_LIMIT
    logger.info "Catalogue: entered GET /api/v2/aws-services?#{query_string}"

    # Split keys in meta_data and data
    # Then transform 'string' params Hash into keys
    keyed_params = add_descriptor_level('awsd', params)

    # Set headers
    case request.content_type
      when 'application/x-yaml'
        headers = { 'Accept' => 'application/x-yaml', 'Content-Type' => 'application/x-yaml' }
      else
        headers = { 'Accept' => 'application/json', 'Content-Type' => 'application/json' }
    end
    headers[:params] = params unless params.empty?

    # Get rid of :offset and :limit
    [:offset, :limit].each { |k| keyed_params.delete(k) }

    # Check for special case (:version param == last)
    if keyed_params.key?(:'awsd.version') && keyed_params[:'awsd.version'] == 'last'
      # Do query for last version -> get_awsd_ns_vendor_last_version
      keyed_params.delete(:'awsd.version')

      awss = Awsd.where((keyed_params)).sort({ 'awsd.version' => -1 }) #.limit(1).first()
      logger.info "Catalogue: AWSDs=#{awss}"

      if awss && awss.size.to_i > 0
        logger.info "Catalogue: leaving GET /api/v2/aws-services?#{query_string} with #{awss}"

        awss_list = []
        checked_list = []

        awss_name_vendor = Pair.new(awss.first.awsd['name'], awss.first.awsd['vendor'])
        checked_list.push(awss_name_vendor)
        awss_list.push(awss.first)

        awss.each do |awsd|
          if (awsd.awsd['name'] != awss_name_vendor.one) || (awsd.awsd['vendor'] != awss_name_vendor.two)
            awss_name_vendor = Pair.new(awsd.awsd['name'], awsd.awsd['vendor'])
          end
          awss_list.push(awsd) unless checked_list.any? { |pair| pair.one == awss_name_vendor.one &&
              pair.two == awss_name_vendor.two }
          checked_list.push(awss_name_vendor)
        end
      else
        logger.info "Catalogue: leaving GET /api/v2/aws-services?#{query_string} with 'No AWSDs were found'"
        awss_list = []
      end
      awss = apply_limit_and_offset(awss_list, offset=params[:offset], limit=params[:limit])

    else
      # Do the query
      awss = Awsd.where(keyed_params)
      # Set total count for results
      headers 'Record-Count' => awss.count.to_s
      logger.info "Catalogue: AWSDs=#{awss}"
      if awss && awss.size.to_i > 0
        logger.info "Catalogue: leaving GET /api/v2/aws-services?#{query_string} with #{awss}"
        # Paginate results
        awss = awss.paginate(offset: params[:offset], limit: params[:limit])
      else
        logger.info "Catalogue: leaving GET /api/v2/aws-services?#{query_string} with 'No AWSDs were found'"
      end
    end

    response = ''
    case request.content_type
      when 'application/json'
        response = awss.to_json
      when 'application/x-yaml'
        response = json_to_yaml(awss.to_json)
      else
        halt 415
    end
    halt 200, {'Content-type' => request.content_type}, response
  end

  # @method get_ns_sp_ns_id
  # @overload get '/catalogues/aws-services/:id/?'
  #	  GET one specific descriptor
  #	  @param :id [Symbol] unique identifier
  # Show a NS by internal ID (uuid)
  get '/aws-services/:id/?' do
    unless params[:id].nil?
      logger.debug "Catalogue: GET /api/v2/aws-services/#{params[:id]}"

      begin
        aws = Awsd.find(params[:id])
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "The AWS ID #{params[:id]} does not exist" unless aws
      end
      logger.debug "Catalogue: leaving GET /api/v2/aws-services/#{params[:id]}\" with AWSD #{aws}"

      response = ''
      case request.content_type
        when 'application/json'
          response = aws.to_json
        when 'application/x-yaml'
          response = json_to_yaml(aws.to_json)
        else
          halt 415
      end
      halt 200, {'Content-type' => request.content_type}, response

    end
    logger.debug "Catalogue: leaving GET /api/v2/aws-services/#{params[:id]} with 'No AWSD ID specified'"
    json_error 400, 'No AWSD ID specified'
  end

  # @method post_nss
  # @overload post '/catalogues/aws-services'
  # Post a NS in JSON or YAML format
  post '/aws-services' do
    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    # Compatibility support for YAML content-type
    case request.content_type
      when 'application/x-yaml'
        # Validate YAML format
        # When updating a AWSD, the json object sent to API must contain just data inside
        # of the AWSD, without the json field awsd: before
        aws, errors = parse_yaml(request.body.read)
        halt 400, errors.to_json if errors

        # Translate from YAML format to JSON format
        new_aws_json = yaml_to_json(aws)

        # Validate JSON format
        new_aws, errors = parse_json(new_aws_json)
        halt 400, errors.to_json if errors

      else
        # Compatibility support for JSON content-type
        # Parses and validates JSON format
        new_aws, errors = parse_json(request.body.read)
        halt 400, errors.to_json if errors
    end

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    # Validate AWS
    json_error 400, 'ERROR: AWS Vendor not found' unless new_aws.has_key?('vendor')
    json_error 400, 'ERROR: AWS Name not found' unless new_aws.has_key?('name')
    json_error 400, 'ERROR: AWS Version not found' unless new_aws.has_key?('version')

    # Check if AWS already exists in the catalogue by name, vendor and version
    begin
      aws = Awsd.find_by({ 'awsd.name' => new_aws['name'], 'awsd.vendor' => new_aws['vendor'],
                         'awsd.version' => new_aws['version'] })
      json_return 200, 'Duplicated AWS Name, Vendor and Version'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end
    # Check if AWSD has an ID (it should not) and if it already exists in the catalogue
    begin
      aws = Awsd.find_by({ '_id' => new_aws['_id'] })
      json_return 200, 'Duplicated AWS ID'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    if keyed_params.key?(:username)
      username = keyed_params[:username]
    else
      username = nil
    end

    # Save to DB
    begin
      new_awsd = {}
      new_awsd['awsd'] = new_aws
      # Generate the UUID for the descriptor
      new_awsd['_id'] = SecureRandom.uuid
      new_awsd['status'] = 'active'
      # Signature will be supported
      new_awsd['signature'] = nil
      new_awsd['md5'] = checksum new_aws.to_s
      new_awsd['username'] = username
      aws = Awsd.create!(new_awsd)
    rescue Moped::Errors::OperationFailure => e
      json_return 200, 'Duplicated AWS ID' if e.message.include? 'E11000'
    end

    puts 'New AWS has been added'
    response = ''
    case request.content_type
      when 'application/json'
        response = aws.to_json
      when 'application/x-yaml'
        response = json_to_yaml(aws.to_json)
      else
        halt 415
    end
    halt 201, {'Content-type' => request.content_type}, response
  end

  # @method update_nss
  # @overload put '/catalogues/aws-services/?'
  # Update a NS by vendor, name and version in JSON or YAML format
  ## Catalogue - UPDATE
  put '/aws-services/?' do
    logger.info "Catalogue: entered PUT /api/v2/aws-services?#{query_string}"

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    # Return 400 if params are empty
    json_error 400, 'Update parameters are null' if keyed_params.empty?

    # Compatibility support for YAML content-type
    case request.content_type
      when 'application/x-yaml'
        # Validate YAML format
        # When updating a AWSD, the json object sent to API must contain just data inside
        # of the AWSD, without the json field awsd: before
        aws, errors = parse_yaml(request.body.read)
        halt 400, errors.to_json if errors

        # Translate from YAML format to JSON format
        new_aws_json = yaml_to_json(aws)

        # Validate JSON format
        new_aws, errors = parse_json(new_aws_json)
        halt 400, errors.to_json if errors

      else
        # Compatibility support for JSON content-type
        # Parses and validates JSON format
        new_aws, errors = parse_json(request.body.read)
        halt 400, errors.to_json if errors
    end

    # Validate NS
    # Check if mandatory fields Vendor, Name, Version are included
    json_error 400, 'ERROR: AWS Vendor not found' unless new_aws.has_key?('vendor')
    json_error 400, 'ERROR: AWS Name not found' unless new_aws.has_key?('name')
    json_error 400, 'ERROR: AWS Version not found' unless new_aws.has_key?('version')

    # Set headers
    case request.content_type
      when 'application/x-yaml'
        headers = { 'Accept' => 'application/x-yaml', 'Content-Type' => 'application/x-yaml' }
      else
        headers = { 'Accept' => 'application/json', 'Content-Type' => 'application/json' }
    end
    headers[:params] = params unless params.empty?

    # Retrieve stored version
    if keyed_params[:vendor].nil? && keyed_params[:name].nil? && keyed_params[:version].nil?
      json_error 400, 'Update Vendor, Name and Version parameters are null'
    else
      begin
        aws = Awsd.find_by({ 'awsd.vendor' => keyed_params[:vendor], 'awsd.name' => keyed_params[:name],
                           'awsd.version' => keyed_params[:version] })
        puts 'AWS is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        json_error 404, "The AWSD Vendor #{keyed_params[:vendor]}, Name #{keyed_params[:name]}, Version #{keyed_params[:version]} does not exist"
      end
    end
    # Check if AWS already exists in the catalogue by Name, Vendor and Version
    begin
      aws = Awsd.find_by({ 'awsd.name' => new_aws['name'], 'awsd.vendor' => new_aws['vendor'],
                         'awsd.version' => new_aws['version'] })
      json_return 200, 'Duplicated AWS Name, Vendor and Version'
    rescue Mongoid::Errors::DocumentNotFound => e
      # Continue
    end

    if keyed_params.key?(:username)
      username = keyed_params[:username]
    else
      username = nil
    end

    # Update to new version
    puts 'Updating...'
    new_awsd = {}
    new_awsd['_id'] = SecureRandom.uuid # Unique UUIDs per AWSD entries
    new_awsd['awsd'] = new_aws
    new_awsd['status'] = 'active'
    new_awsd['signature'] = nil
    new_awsd['md5'] = checksum new_aws.to_s
    new_awsd['username'] = username

    begin
      new_aws = Awsd.create!(new_awsd)
    rescue Moped::Errors::OperationFailure => e
      json_return 200, 'Duplicated AWS ID' if e.message.include? 'E11000'
    end
    logger.debug "Catalogue: leaving PUT /api/v2/aws-services?#{query_string}\" with AWSD #{new_aws}"

    response = ''
    case request.content_type
      when 'application/json'
        response = new_aws.to_json
      when 'application/x-yaml'
        response = json_to_yaml(new_aws.to_json)
      else
        halt 415
    end
    halt 200, {'Content-type' => request.content_type}, response
  end

  # @method update_nss_id
  # @overload put '/catalogues/aws-services/:id/?'
  # Update a NS in JSON or YAML format
  ## Catalogue - UPDATE
  put '/aws-services/:id/?' do
    # Return if content-type is invalid
    halt 415 unless (request.content_type == 'application/x-yaml' or request.content_type == 'application/json')

    unless params[:id].nil?
      logger.debug "Catalogue: PUT /api/v2/aws-services/#{params[:id]}"

      # Transform 'string' params Hash into keys
      keyed_params = keyed_hash(params)

      # Check for special case (:status param == <new_status>)
      if keyed_params.key?(:status)
        # Do update of Descriptor status -> update_ns_status
        logger.info "Catalogue: entered PUT /api/v2/aws-services/#{query_string}"

        # Validate NS
        # Retrieve stored version
        begin
          puts 'Searching ' + params[:id].to_s
          aws = Awsd.find_by({ '_id' => params[:id] })
          puts 'AWS is found'
        rescue Mongoid::Errors::DocumentNotFound => e
          json_error 404, 'This AWSD does not exists'
        end

        # Validate new status
        valid_status = %w(active inactive delete)
        if valid_status.include? keyed_params[:status]
          # Update to new status
          begin
            aws.update_attributes(status: keyed_params[:status])
          rescue Moped::Errors::OperationFailure => e
            json_error 400, 'ERROR: Operation failed'
          end
        else
          json_error 400, "Invalid new status #{keyed_params[:status]}"
        end
        halt 200, "Status updated to {#{query_string}}"

      else
        # Compatibility support for YAML content-type
        case request.content_type
          when 'application/x-yaml'
            # Validate YAML format
            # When updating a AWSD, the json object sent to API must contain just data inside
            # of the AWSD, without the json field awsd: before
            aws, errors = parse_yaml(request.body.read)
            halt 400, errors.to_json if errors

            # Translate from YAML format to JSON format
            new_aws_json = yaml_to_json(aws)

            # Validate JSON format
            new_aws, errors = parse_json(new_aws_json)
            halt 400, errors.to_json if errors

          else
            # Compatibility support for JSON content-type
            # Parses and validates JSON format
            new_aws, errors = parse_json(request.body.read)
            halt 400, errors.to_json if errors
        end

        # Validate AWS
        # Check if mandatory fields Vendor, Name, Version are included
        json_error 400, 'ERROR: AWS Vendor not found' unless new_aws.has_key?('vendor')
        json_error 400, 'ERROR: AWS Name not found' unless new_aws.has_key?('name')
        json_error 400, 'ERROR: AWS Version not found' unless new_aws.has_key?('version')

        # Retrieve stored version
        begin
          puts 'Searching ' + params[:id].to_s
          aws = Awsd.find_by({ '_id' => params[:id] })
          puts 'AWS is found'
        rescue Mongoid::Errors::DocumentNotFound => e
          json_error 404, "The AWSD ID #{params[:id]} does not exist"
        end

        # Check if AWS already exists in the catalogue by name, vendor and version
        begin
          aws = Awsd.find_by({ 'awsd.name' => new_aws['name'], 'awsd.vendor' => new_aws['vendor'],
                             'awsd.version' => new_aws['version'] })
          json_return 200, 'Duplicated AWS Name, Vendor and Version'
        rescue Mongoid::Errors::DocumentNotFound => e
          # Continue
        end

        if keyed_params.key?(:username)
          username = keyed_params[:username]
        else
          username = nil
        end

        # Update to new version
        puts 'Updating...'
        new_awsd = {}
        new_awsd['_id'] = SecureRandom.uuid # Unique UUIDs per AWSD entries
        new_awsd['awsd'] = new_aws
        new_awsd['status'] = 'active'
        new_awsd['signature'] = nil
        new_awsd['md5'] = checksum new_aws.to_s
        new_awsd['username'] = username

        begin
          new_aws = Awsd.create!(new_awsd)
        rescue Moped::Errors::OperationFailure => e
          json_return 200, 'Duplicated AWS ID' if e.message.include? 'E11000'
        end
        logger.debug "Catalogue: leaving PUT /api/v2/aws-services/#{params[:id]}\" with AWSD #{new_aws}"

        response = ''
        case request.content_type
          when 'application/json'
            response = new_aws.to_json
          when 'application/x-yaml'
            response = json_to_yaml(new_aws.to_json)
          else
            halt 415
        end
        halt 200, {'Content-type' => request.content_type}, response
      end
    end
    logger.debug "Catalogue: leaving PUT /api/v2/aws-services/#{params[:id]} with 'No AWSD ID specified'"
    json_error 400, 'No AWSD ID specified'
  end

  # @method delete_awsd_sp_ns
  # @overload delete '/aws-services/?'
  #	Delete a AWS by vendor, name and version
  delete '/aws-services/?' do
    logger.info "Catalogue: entered DELETE /api/v2/aws-services?#{query_string}"

    # Transform 'string' params Hash into keys
    keyed_params = keyed_hash(params)

    unless keyed_params[:vendor].nil? && keyed_params[:name].nil? && keyed_params[:version].nil?
      begin
        aws = Awsd.find_by({ 'awsd.vendor' => keyed_params[:vendor], 'awsd.name' => keyed_params[:name],
                           'awsd.version' => keyed_params[:version]} )
        puts 'AWS is found'
      rescue Mongoid::Errors::DocumentNotFound => e
        json_error 404, "The AWSD Vendor #{keyed_params[:vendor]}, Name #{keyed_params[:name]}, Version #{keyed_params[:version]} does not exist"
      end
      logger.debug "Catalogue: leaving DELETE /api/v2/aws-services?#{query_string}\" with AWSD #{aws}"
      aws.destroy
      halt 200, 'OK: AWSD removed'
    end
    logger.debug "Catalogue: leaving DELETE /api/v2/aws-services?#{query_string} with 'No AWSD Vendor, Name, Version specified'"
    json_error 400, 'No AWSD Vendor, Name, Version specified'
  end

  # @method delete_awsd_sp_ns_id
  # @overload delete '/catalogues/network-service/:id/?'
  #	  Delete a NS by its ID
  #	  @param :id [Symbol] unique identifier
  # Delete a NS by uuid
  delete '/aws-services/:id/?' do
    unless params[:id].nil?
      logger.debug "Catalogue: DELETE /api/v2/aws-services/#{params[:id]}"
      begin
        aws = Awsd.find(params[:id])
      rescue Mongoid::Errors::DocumentNotFound => e
        logger.error e
        json_error 404, "The AWSD ID #{params[:id]} does not exist" unless aws
      end
      logger.debug "Catalogue: leaving DELETE /api/v2/aws-services/#{params[:id]}\" with AWSD #{aws}"
      aws.destroy
      halt 200, 'OK: AWSD removed'
    end
    logger.debug "Catalogue: leaving DELETE /api/v2/aws-services/#{params[:id]} with 'No AWSD ID specified'"
    json_error 400, 'No AWSD ID specified'
  end
end
