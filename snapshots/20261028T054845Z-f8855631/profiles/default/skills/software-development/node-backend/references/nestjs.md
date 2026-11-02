# NestJS Reference

## When to Reach for NestJS

Use NestJS when you want strong conventions, modular architecture, dependency injection, decorators, guards, interceptors, pipes, and a framework that scales well across large TypeScript backend teams.

## Baseline Structure

```text
src/
├── main.ts
├── app.module.ts
├── common/
│   ├── filters/
│   ├── guards/
│   ├── interceptors/
│   └── pipes/
└── modules/
    └── users/
        ├── users.module.ts
        ├── users.controller.ts
        ├── users.service.ts
        ├── dto/
        └── entities/
```

## Core Patterns

### Module boundaries

Each feature should own its controller, service, DTOs, and persistence integration. Keep modules focused and avoid a giant shared dumping ground.

### Controllers stay thin

```ts
@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get(':id')
  findOne(@Param('id', ParseUUIDPipe) id: string) {
    return this.usersService.findById(id);
  }
}
```

### Services own business logic

```ts
@Injectable()
export class UsersService {
  async findById(id: string) {
    const user = await this.repo.findOne({ where: { id } });
    if (!user) throw new NotFoundException('User not found');
    return user;
  }
}
```

## Validation

Prefer DTOs with `class-validator` and `class-transformer`, plus global validation pipes.

```ts
app.useGlobalPipes(new ValidationPipe({
  whitelist: true,
  forbidNonWhitelisted: true,
  transform: true,
}));
```

```ts
export class CreateUserDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(2)
  name: string;
}
```

## Cross-Cutting Concerns

Use Nest primitives consistently:
- **Guards** for auth/authorization
- **Interceptors** for response shaping, timing, logging
- **Filters** for exception mapping
- **Pipes** for parsing/validation

## Config

Prefer typed config access and centralized environment validation. Avoid scattering direct `process.env.X` reads across services.

## Testing

- Unit test services with mocked providers
- Integration test controllers/modules with Nest testing utilities
- Use e2e tests for full HTTP workflows

## Common Pitfalls

1. Putting too much logic in controllers.
2. Skipping global validation pipes.
3. Exporting everything from every module.
4. Treating providers as global when they should stay module-scoped.
5. Mixing framework exceptions and ad-hoc error objects.

## Checklist

- [ ] Feature modules have clear boundaries
- [ ] Controllers delegate to services
- [ ] ValidationPipe is configured globally
- [ ] Guards/filters/interceptors are used for cross-cutting concerns
- [ ] Services are testable with injected dependencies
